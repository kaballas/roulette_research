# C3 — coverage solver and candidate frontier research

Registered 13 October 2026 before the new benchmark runs. Original C2 evidence
is preserved. Hypothesis: explicit feasibility searches, verified incumbent
bounds and stronger payout-lattice constraints improve useful certificates and
incumbents for the same finite allocation problem. Success means improved
verified allocations or tighter valid bounds, with honest unresolved statuses;
no result changes the fair-wheel expectation.

Model: all 157 selected standard European positions; exactly 20 integer chips;
at most ten occupied positions; minimum profitable-pocket targets
26,28,30,32,34 (70,75,80,85,90%). Strict profit means at least one chip after
subtracting every component stake. Maximise minimum pocket profit. First seek
feasibility; then solve worst-loss optimisation with the best exactly verified
available incumbent as a valid floor constraint. A known feasible seed may
short-circuit the feasibility stage. CP-SAT may additionally use allocation
hints. HiGHS has no claimed warm-start interface through scipy.optimize.milp.

Registered tiers are **C3-060**, **C3-300**, **C3-900**, with respectively 60,
300 and 900 solver seconds per target per stage per available backend. Each
tier is a separate fresh artefact, not a replacement of another run. Execute
C3-060 first. Longer tiers remain explicitly not tested until their own commands
are executed and evidence retained; do not infer their outcomes from C3-060.
Backends: SciPy/HiGHS and optional OR-Tools CP-SAT. An unavailable dependency
must be reported as unavailable, never substituted or counted as a benchmark.
Both backends receive the same seed pool snapshot for each target; solutions
can inform later targets. This is a workflow benchmark with incumbent reuse,
not an isolated cold-start algorithm comparison.

Constructive benchmark: five disjoint six-lines, four chips each, total20,
30 profitable pockets, worst loss20. Also exactly revalidate retained C2
allocations before reusing them. Record each stage, timeout, elapsed time,
available solver gap and bound, exact allocated stakes, all37 profits and
full distribution. Retain no-incumbent and infeasibility outcomes. Verify
sum of pocket profits=-20, expected profit=-20/37 and return per chip=-1/37.
Source hashes, dependency versions, registration hash and actual Git revision
(where available) identify the code. No data split, RNG, confidence interval or
statistical multiple-testing correction applies to exact one-spin calculations.

For each pocket, let d be the gcd of all available positive gross payout
multipliers. Gross receipts are multiples of d. Any chosen minimum profit t
therefore requires at least d*ceil(max(0,20+t)/d) receipts on that pocket;
a profitable pocket requires at least d*ceil(21/d). Add the smallest necessary
increments for the required number of profitable pockets. If this sum exceeds
720 total gross receipts, that floor or target is impossible. This is a
necessary bound only. No symmetry breaking is permitted without proving
catalogue invariance and preservation of the objective and feasible orbits.

Separate exact evaluation computes conditional mean profit on wins, conditional
loss magnitude on losing outcomes and upper-tail expected shortfall of
loss=-profit at alpha=1/20, including fractional mass at the boundary. Retain
the nondominated supplied candidates on positive-pocket count (larger), minimum
profit (larger) and expected shortfall (smaller). All compared portfolios must
have the same20-chip outlay. This is a candidate Pareto frontier, not proof of
the complete globally Pareto-optimal set; no arbitrary weighted score.

Full bankroll/session evaluation stays separate from the one-spin solver.
This cycle adds no strategies, prediction models or real-money actions.
Session survival at100/500/1000 spins remains not tested until a separate
bankroll, affordability, stopping-rule and uncertainty registration is run.

Acceptance: independent exact scalar settlement of every retained allocation,
small-instance exhaustive solver comparisons, pytest, static and formatting
checks where tooling is available, and an independent adversarial review.
CI configuration is evidence of configured checks; a successful hosted run
must be observed before claiming demonstrated GitHub CI execution.

Pre-run mathematical addition: for B20 and34 profitable pockets, a modulo3
argument strengthens the worst-profit upper bound to-20. All non-even-money
gross multipliers are divisible by3; the729 even-money stake residue patterns
have either zero or at least16 numbered pockets with nonzero gross residues.
The total gross budget720 and34 minimum gross receipts21 allow at most nine
such pockets. Thus all receipts are multiples of3; avoiding a zero receipt
would cost at least34*21+3*3=723. This proves any feasible90% allocation has
a full20-chip loss somewhere, without establishing its feasibility. See
`docs/MATHEMATICS.md` for the argument; independently rerun the finite lemma.
