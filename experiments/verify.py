"""Verify saved numerical evidence with current code and retain a source manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from baseline import ROOT, metadata
from roulette.evaluation import evaluate_sessions
from roulette.rules import RED, STRAIGHT_ZERO, Wheel
from roulette.simulation import simulate_sessions, simulate_wagers
from roulette.statistics import mean_interval
from roulette.strategies import NAMES, SECTOR, MIXED
from roulette.theory import moments


def require(condition: bool, message: str) -> None:
    """Reject invalid evidence even when Python runs with optimisation enabled."""
    if not condition:
        raise ValueError(message)


def validate_cases(baseline: dict, strategies: dict) -> None:
    """Require the complete registered cases, with no duplicates or substitutions."""
    expected_baseline = {(w.value, b.name) for w in Wheel for b in (RED, STRAIGHT_ZERO)}
    actual_baseline = [(r["wheel"], r["bet"]) for r in baseline["results"]]
    require(len(actual_baseline) == len(expected_baseline)
            and set(actual_baseline) == expected_baseline,
            "Baseline evidence must contain all eight distinct registered cases")
    configurations = [(name, RED.name, 1) for name in NAMES]
    configurations += [("flat", SECTOR.name, 6), ("flat", MIXED.name, 2)]
    expected_strategies = {(w.value, name, bet, base)
                          for w in (Wheel.EUROPEAN, Wheel.AMERICAN)
                          for name, bet, base in configurations}
    actual_strategies = [(r["wheel"], r["strategy"], r["bet"], r["base"])
                         for r in strategies["results"]]
    require(len(actual_strategies) == len(expected_strategies)
            and set(actual_strategies) == expected_strategies,
            "Strategy evidence must contain all sixteen distinct registered cases")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "verification.json")
    parser.add_argument("--baseline", type=Path, default=ROOT / "results" / "baseline.json")
    parser.add_argument("--strategies", type=Path, default=ROOT / "results" / "strategies.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    test = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT,
                          text=True, capture_output=True)
    print(test.stdout, end="", flush=True)
    if test.returncode:
        print(test.stderr, file=sys.stderr)
        raise SystemExit(test.returncode)
    baseline = json.loads(args.baseline.read_text())
    strategies = json.loads(args.strategies.read_text())
    validate_cases(baseline, strategies)
    for row in baseline["results"]:
        wheel = Wheel(row["wheel"])
        bet = RED if row["bet"] == RED.name else STRAIGHT_ZERO
        mean, variance = moments(wheel, bet)
        require(str(mean) == row["exact_ev"] and str(variance) == row["exact_variance"],
                f"Exact moments mismatch: {row['wheel']} / {row['bet']}")
        current = mean_interval(simulate_wagers(wheel, bet, row["n"], row["seed"]), 8)
        require(current == row["interval"], f"Baseline interval mismatch: {row}")
        covered = current["low"] <= float(mean) <= current["high"]
        require(row["covered"] == covered and covered, f"Baseline coverage failed: {row}")
    c = strategies["configuration"]
    bets = {bet.name: bet for bet in (RED, SECTOR, MIXED)}
    for row in strategies["results"]:
        data = simulate_sessions(Wheel(row["wheel"]), bets[row["bet"]], row["strategy"],
                                 c["sessions"], c["max_wagers"], c["bankroll"],
                                 c["table_min"], c["table_max"], row["seed"], row["base"])
        h = 1 / (37 if Wheel(row["wheel"]) == Wheel.EUROPEAN else 19)
        require(row["house_edge"] == h, f"Incorrect analytical house edge: {row}")
        current = evaluate_sessions(data, h, c["interval_comparisons"])
        require(all(value == row[key] for key, value in current.items()),
                f"Strategy summary mismatch: {row}")
        residual = current["staking_identity_residual"]
        ratio = current["return_per_unit_staked"]
        residual_covered = residual["low"] <= 0 <= residual["high"]
        return_covered = ratio["low"] <= -h <= ratio["high"]
        require(row["residual_covers_zero"] == residual_covered and residual_covered,
                f"Staking identity reconciliation failed: {row}")
        require(row["return_covers_benchmark"] == return_covered and return_covered,
                f"Return reconciliation failed: {row}")
        require(current["mean_profit"]["high"] < 0, f"Profit interval includes zero: {row}")
    evidence = {"date": "2026-10-12", "metadata": metadata(),
                "pytest_output": test.stdout.strip(), "pytest_exit_code": test.returncode,
                "baseline_cases_exactly_replayed": len(baseline["results"]),
                "strategy_cases_exactly_replayed": len(strategies["results"]),
                "note": "Replayed numerical summaries and checked registered case coverage; timing and original source metadata excluded.",
                "evidence_paths": {"baseline.json": str(args.baseline.resolve()),
                                   "strategies.json": str(args.strategies.resolve())},
                "document_sha256": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "pyproject.toml",
                              *sorted((ROOT / "docs").glob("*.md"))]},
                "evidence_sha256": {
                    name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for name, path in (("baseline.json", args.baseline),
                                       ("strategies.json", args.strategies))}}
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Exactly replayed {len(baseline['results'])} baseline and "
          f"{len(strategies['results'])} strategy cases; evidence retained.")


if __name__ == "__main__":
    main()
