# Implementation plan

1. Independently derive exact payout distributions and variance, implement rules,
   and predeclare validation with separate mathematical, simulation and audit agents.
2. Test rules before running fixed-seed, precision-sized fair-wheel experiments.
   Hypothesis: completed unit wagers agree with exact EV within simultaneous
   approximate 99% confidence intervals (Bonferroni, eight comparisons).
3. After that gate, compare finite-bankroll flat and Martingale strategies, then
   the remaining Phase 2 strategies, with explicit limits and settlement.
   Hypothesis: risk profiles change while expected profit remains negative;
   for standard bets E[profit + house_edge * turnover] = 0.
4. Independently review code and findings; resolve defects, rerun relevant tests,
   record evidence and reproducible commands in the research ledger.

No externally sourced data or real betting is involved. No Git repository was
present initially; evidence will identify code by SHA-256 source manifest.

Coverage optimisation cycle (C2-001): prioritise mixed legal bet types and
unequal integer chip allocations over further staking simulations. Register a
20-chip budget, at most ten occupied positions, and 70/75/80/85/90% profitable
spin targets before runs. Minimise worst-case loss; independently re-settle
all 37 outcomes and verify EV=-20/37. Compare solver bounds with exact
analytical bounds, preserve incomplete statuses, and test against a small
independent exhaustive oracle. Record scope, certificates and remaining gaps.
