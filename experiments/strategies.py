"""Run P2-001: PYTHONPATH=src python experiments/strategies.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from baseline import ROOT, metadata
from roulette.evaluation import evaluate_sessions
from roulette.rules import Wheel, RED
from roulette.simulation import simulate_sessions
from roulette.strategies import NAMES, SECTOR, MIXED


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "strategies.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve existing evidence: {args.output}")
    rows = []
    configs = [(name, RED, 1) for name in NAMES] + [("flat", SECTOR, 6), ("flat", MIXED, 2)]
    for wheel in (Wheel.EUROPEAN, Wheel.AMERICAN):
        h = 1 / (37 if wheel == Wheel.EUROPEAN else 19)
        for strategy, bet, base in configs:
            seed = 2026101300 + len(rows)
            start = time.perf_counter()
            data = simulate_sessions(wheel, bet, strategy, 20000, 100, 100, 1, 64, seed, base)
            summary = evaluate_sessions(data, h, 48)
            residual = summary["staking_identity_residual"]
            ratio = summary["return_per_unit_staked"]
            summary.update({"wheel": wheel.value, "strategy": strategy, "bet": bet.name,
                            "base": base, "seed": seed, "house_edge": h,
                            "elapsed_seconds": time.perf_counter() - start,
                            "residual_covers_zero": residual["low"] <= 0 <= residual["high"],
                            "return_covers_benchmark": ratio["low"] <= -h <= ratio["high"]})
            rows.append(summary)
            print(wheel.value, strategy, bet.name, "return", round(ratio["estimate"], 5),
                  "mean_profit", round(summary["mean_profit"]["estimate"], 3),
                  "residual_agrees", summary["residual_covers_zero"], flush=True)
    result = {"experiment": "P2-001", "metadata": metadata(),
              "configuration": {"sessions": 20000, "max_wagers": 100, "bankroll": 100,
                                "table_min": 1, "table_max": 64, "alpha_family": .01,
                                "interval_comparisons": 48}, "results": rows}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if not all(r["residual_covers_zero"] and r["return_covers_benchmark"] for r in rows):
        raise SystemExit("Reconciliation miss retained: investigate without retuning")


if __name__ == "__main__":
    main()
