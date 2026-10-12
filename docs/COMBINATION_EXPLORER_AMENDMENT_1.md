# C4 amendment 1 — 90 s tier and method changes (dated 2026-10-13)

Amends `docs/COMBINATION_EXPLORER_REGISTER.md`, which is left unchanged so that
the `registration_sha256` recorded in the preserved 30 s evidence still
resolves (`2f5d7468…be5a`).

## Tiers

| Tier | Output | MILP seconds | Twin tolerance | Code state |
| --- | --- | ---: | --- | --- |
| C4-001 / 30 s | `results/combination-explorer-20chips-10bets-030s.{json,md}` | 30 | `3*count` | before amendment fixes below |
| C4-001 / 90 s | `results/combination-explorer-20chips-10bets-090s.{json,md}` (written when the run completes) | 90 | `count` | after the fixes below |

The 90 s tier was chosen **after** seeing the 30 s outcome: several cells were
under-resolved (80% `tail` returned 0 of 10; 70% `worst_loss` missed the known
proved optimum of -5 chips). The 30 s tier is therefore **inconclusive** for
ranking quality, although every portfolio in it is exactly settled and valid.
A separate single-cell probe at 120 s reached -5 chips at 70% and found a
80% tail incumbent; that probe was exploratory and is not part of the evidence.

## Method differences between the tiers (all of them)

1. Solver time per MILP: 30 s → 90 s.
2. P&L-twin tolerance before stopping a cell: `3*count` → `count`.
3. Reference row A: the 30 s run picked the recorded portfolio with the best
   worst loss regardless of objective or stake mode; the 90 s run ranks by the
   cell's exact objective and, in equal-stake cells, accepts only equal-chip
   references (no equal-stake cell is in the grid).
4. Reference exclusion: matched by name in the 30 s run, by physical identity
   (numbers, payout) in the 90 s run; for catalogue-standard names the two
   coincide.
5. Tail objective scaled to `alpha*eta + sum(u)/37` (same minimiser as
   `eta + sum(u)/(37*alpha)`); `alpha` restricted to [1e-6, 1].

Items 3–5 were prompted by an independent adversarial review.

## Scope of the distinctness guarantee

Bet-set distance and sorted-P&L deduplication apply **among explorer rows**.
Row A (the recorded reference) is only kept at bet-set distance from explorer
rows; it may be a P&L twin of an explorer row, and several cells show this.
Row A is context, not an explorer output.

## Stop reasons

`count_reached`; `exhausted` (solver reports no further portfolio at the
distance, numerical evidence); `analytical_infeasible` (exact lattice
argument); `time_limit` (a solve ended with no incumbent, which is not proof
that none exists); `twin_limit` (more than the tolerated number of candidates
repeated an accepted P&L distribution; not exhaustion and not a time limit).
