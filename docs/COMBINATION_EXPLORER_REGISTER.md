# C4 — Roulette Combination Explorer (pre-registration)

Registered before running the C4-001 grid. Date: 2026-10-13.

## Hypothesis and success criterion

H4-1 (constructive): for 20 chips, at most 10 positions, European single-zero
wheel, and targets of 70%, 80% and 90% strictly profitable pockets, the
explorer can return several portfolios per objective whose bet sets differ by
at least 4 positions and whose sorted 37-pocket P&L multisets are all
different.

Success: every returned portfolio passes independent exact settlement, meets
the pocket target, spends exactly the budget and has expectation exactly
`-stake/37`. Cells that return fewer than the requested ten are reported with
their stop reason. Failure to reach ten is a result, not a reason to loosen
`min_distance` after the fact.

## Not claimed

- No portfolio has a positive expectation. Every one has return `-1/37` per
  chip (proved: sum of the 37 pocket profits is `-stake`).
- Lists are best-found distinct alternatives from a time-limited numerical
  MILP. `optimal` is HiGHS numerical evidence; `limit` means best found. They
  are not complete enumerations or certified global rankings.
- A higher profitable-pocket count is not an edge: it trades frequency for
  larger losses on the other pockets.

## Model

Fixed integer chip budget `B`, at most `m` occupied positions, each position a
physical catalogue bet from the selected families (default: split, corner,
street, six-line, dozen, column, even-money; straight-up is excluded unless
requested). Profit on a pocket is `sum(stake*(payout+1) on covering bets) - B`.
Target: at least `ceil(37*pct/100)` pockets with profit `> 0`.

Objectives (all one-spin, minimisation form):

1. `frequency`: maximise profitable pockets, tie-break larger worst profit
   (lexicographic weight `2B+1`).
2. `worst_loss`: maximise the minimum pocket profit.
3. `tail`: minimise expected shortfall of loss at alpha = 1/20 (Rockafellar–
   Uryasev linearisation; the returned value is recomputed exactly by
   `roulette.coverage_risk.exact_risk`). `alpha` must lie in [1e-6, 1];
   the solver minimises `alpha*eta + sum(u)/37`.

Under `frequency` the target is only a floor, so lists for different targets
may coincide; that is expected and reported as is.

Stake modes: `any` (arbitrary positive integer chips) and `equal` (the same
chips on every occupied position, position count must divide `B`).

Distinctness: (a) Hamming distance on the occupied bet set at least
`min_distance` (default 4) from every earlier portfolio and from the reference
portfolio; (b) a portfolio whose sorted 37-pocket P&L multiset repeats an
accepted one (mirror or shifted twin) is discarded; at most `3*count` such
twins are tolerated, then the cell stops with `twin_limit`. Restaking the same
bet set is therefore never a new alternative.

Reference (row A): the best exact-checked recorded portfolio for the same
budget, position limit, target, objective (ranked by the same exact objective)
and stake mode (equal-stake cells accept only equal-chip references) from `results/coverage-benchmark-060.json`
and `results/coverage-optimisation-20chips.json`, when present.

## Initial grid (C4-001)

20 chips, 10 positions, targets 70/80/90, three objectives, `any` stakes,
count 10, `min_distance` 4, 30 s per MILP. Wider budget/position grids are
exploratory follow-ups and recorded separately.

Reference exclusion matches bets by physical identity (numbers, payout), not
name. An independent adversarial review run before the grid found and led to
fixes of reference selection, reference exclusion and small-alpha handling.

## Acceptance

Exact settlement of every output, `pytest -q`, a brute-force comparison on a
small catalogue, and an independent adversarial review before any ledger
entry is upgraded.
