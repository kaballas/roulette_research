"""Run predeclared Phase 1 checks: PYTHONPATH=src python experiments/baseline.py."""
from __future__ import annotations

import hashlib
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import scipy
import sympy

from roulette.rules import Wheel, RED, STRAIGHT_ZERO
from roulette.theory import moments
from roulette.simulation import simulate_wagers
from roulette.statistics import mean_interval, required_sample_size

ROOT = Path(__file__).resolve().parents[1]


def manifest() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("src", "experiments", "tests")
            for p in sorted((ROOT / folder).rglob("*.py"))}


def metadata() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "sympy": sympy.__version__,
            "code_sha256": manifest(), "rng": "NumPy default_rng / PCG64"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "baseline.json")
    args = parser.parse_args()
    rows = []
    for i, (wheel, bet) in enumerate((w, b) for w in Wheel for b in (RED, STRAIGHT_ZERO)):
        mean, variance = moments(wheel, bet)
        n = required_sample_size(float(variance), .03, 8)
        seed = 2026101200 + i
        values = simulate_wagers(wheel, bet, n, seed)
        interval = mean_interval(values, 8)
        rows.append({"wheel": wheel.value, "bet": bet.name, "n": n, "seed": seed,
                     "exact_ev": str(mean), "exact_variance": str(variance),
                     "interval": interval,
                     "covered": interval["low"] <= float(mean) <= interval["high"]})
    result = {"experiment": "P1-001", "alpha_family": .01, "comparisons": 8,
              "target_halfwidth": .03, "interval_method": "Bonferroni asymptotic normal",
              "metadata": metadata(), "results": rows}
    path = args.output
    if path.exists():
        raise FileExistsError(f"Preserve existing evidence: {path}")
    path.write_text(json.dumps(result, indent=2) + "\n")
    for row in rows:
        print(row["wheel"], row["bet"], row["n"], row["exact_ev"], row["interval"], row["covered"])
    if not all(row["covered"] for row in rows):
        raise SystemExit("Baseline coverage failed; investigate, do not retune seeds")


if __name__ == "__main__":
    main()
