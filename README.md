# Roulette research lab

Phase 1 has exact mathematical derivations and Monte Carlo corroboration;
it is not formally verified. Phase 2 compares eight fixed strategy configurations
on standard European and American wheels.
On the independent fair-wheel model, every tested configuration has negative
expectation. Staking changes turnover, drawdown and loss tails; it does not
remove the edge. No real-world betting advantage is established.

The configurations are flat stake, Martingale, reverse Martingale, Fibonacci,
d'Alembert and Labouchere on red, plus flat six-number and red/zero portfolios.
The six numbers form a sector only on the European wheel; the American case
uses the same number set. These runs compare specified configurations with
different turnover, not a universal ranking of strategy families.

Python 3.11+:

```sh
python -m pip install -e '.[test]'
pytest -q
PYTHONPATH=src python experiments/baseline.py --output /tmp/roulette-baseline.json
PYTHONPATH=src python experiments/strategies.py --output /tmp/roulette-strategies.json
PYTHONPATH=src python experiments/verify.py \
  --baseline /tmp/roulette-baseline.json \
  --strategies /tmp/roulette-strategies.json \
  --output /tmp/roulette-verification.json
```

Use fresh output paths; experiment entry points refuse to overwrite evidence.
The original aggregates are [baseline.json](results/baseline.json) and
[strategies.json](results/strategies.json). RNG is NumPy PCG64, with fixed seeds
recorded per case. Package versions and SHA-256 source manifests identify each
run; there was no Git repository initially. Replays on different dependency
versions may differ. No raw per-spin files are stored by default.

Read [research ledger](docs/RESEARCH_LEDGER.md), [mathematical derivations](docs/MATHEMATICS.md),
[validation plan](docs/VALIDATION_PLAN.md), [Phase 2 registration](docs/PHASE2_REGISTER.md)
and [adversarial review](docs/ADVERSARIAL_REVIEW.md). The ledger distinguishes
mathematical proofs from Monte Carlo corroboration and documents a Phase 1
registration deviation.

`src/roulette/` separates rules, exact theory, strategies, simulation, statistics
and evaluation. Outcomes 0–36 identify European numbers; 37 identifies American
double zero. Settlement values are net profit, excluding returned stake.

French concessions apply only to qualifying even-money wagers. The selected
en prison convention holds through repeated zeros and resolves outstanding
stakes before a completed-wager horizon; resolution spins add no turnover.
The API accepts fractional stakes, with no
currency rounding or venue-specific chip denominations. Each component must
meet the table minimum and maximum; the total stake must also meet the maximum
and available bankroll. Illegal or unaffordable stakes stop play without
clipping. Drawdown measures settled bankroll. Portfolio simulation supports
standard European/American rules; French portfolios are explicitly rejected.
Synthetic coverage sets need not correspond to bets physically offered at a table.

Board coverage analysis uses a separate catalogue of standard European layout
bets and counts strictly positive net profit after subtracting every stake.
Five disjoint six-lines covering 1–30 at $10 each produce +$10 on 30 pockets
and −$50 on seven: expected profit is −$50/37 per spin. Coverage alone does
not imply profit; six disjoint equal six-lines cover 36 pockets but merely
break even on those outcomes.

```sh
PYTHONPATH=src python experiments/coverage.py --output /tmp/roulette-coverage.json
```

This exhausts the 2,046 distinct equal-chip six-line combinations using one to
ten bets and counts combinations reaching 70%, 75% and 80% profitable outcomes.
Use `--families` to select other catalogue families. A preflight combination
budget rejects oversized searches without truncation. Full-catalogue searches
up to ten bets and unequal stake allocations have not been exhaustively searched.
See the [coverage registration](docs/COVERAGE_REGISTER.md) for assumptions and
the distinction between layout coverage and physical wheel sectors.

Mixed-integer coverage optimisation permits mixed catalogue families and unequal
chip allocations. It fixes a total budget, uses at most ten occupied bet
positions, and minimises the worst one-spin loss subject to a required number
of strictly profitable pockets. The registered default is 20 chips and targets
70%, 75%, 80%, 85% and 90%, with ten solver seconds per target:

```sh
PYTHONPATH=src python experiments/optimise_coverage.py \
  --output /tmp/roulette-coverage-optimisation.json
```

Use `--chip-budget`, `--targets`, `--families` and `--time-limit` for explicitly
different problems. Output includes all 37 exact net profits, the distribution,
selected stakes, solver bounds and termination status. A time limit may leave
optimality or even feasibility unestablished. Numerical solver certificates and
exact analytical certificates are labelled separately. Fixed integer budgets
do not cover every continuous stake ratio. Expected profit remains minus the
total stake divided by 37. See the
[optimisation registration](docs/COVERAGE_OPTIMISATION_REGISTER.md) and
[derivation](docs/MATHEMATICS.md).

The [registered run](results/coverage-optimisation-20chips.json) reached all five
time limits. Retained exact allocations establish 70–80% feasibility; none of
the five optima was established, and 85–90% feasibility remains unresolved.
The [independent audit](results/coverage-optimisation-audit.json) combines
feasible witnesses across targets. The full suite passes 232 tests.

The baseline and session comparisons use RNG; coverage settlement is exact.
Coverage optimisation takes priority over further Martingale comparisons.
There are no external spin data or out-of-sample claims.
Statistical signal testing (the original Phase 3) remains not tested; it requires an identified external data source,
wheel IDs, timestamps, collection method, a multiple-testing plan and a sealed
later-period sample.
