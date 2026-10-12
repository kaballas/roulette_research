# C2-001 — integer allocation and worst-loss optimisation

Registered before the default optimisation runs, 12 October 2026.

Hypothesis: with a fixed total stake and a required probability of strictly
positive profit, mixed legal bets and unequal integer allocations may improve
the worst one-spin loss relative to particular equal-chip examples. Expected
profit remains minus total stake / 37. Optimisation concerns the distribution
of losses and gains, not removal of the house edge.

The default experiment uses all 157 bets in the selected standard European
catalogue, exactly 20 equal-denomination chips in total, and at most ten distinct
active bets. Integer stakes may differ between active bets. Run five separate
targets: at least 70%, 75%, 80%, 85% and 90% strictly profitable outcomes,
respectively 26, 28, 30, 32 and 34 of the 37 equally likely pockets. Each target
receives a ten-second solver time limit. Retain every outcome, including no
incumbent, infeasibility reports and incomplete optimisation. Do not increase
limits or change the budget after observing results and present these as the
registered run. Timings and returned incumbents may vary with hardware and
solver versions; retain versions and source hashes.

For bet i let x_i be its nonnegative integer chip stake, y_i its binary active
indicator, and g_ji its gross return per chip on pocket j (zero for a loss,
otherwise the quoted net payout plus one). Fix sum(x_i)=B=20. Enforce
y_i <= x_i <= B*y_i and sum(y_i)<=10. Pocket profit is
P_j=sum_i(g_ji*x_i)-B. Binary indicators z_j need only imply P_j>=1;
they need not mark every profitable pocket. Enforce sum(z_j)>=r and maximise
t subject to t<=P_j for all 37 pockets. Report the exact realised minimum
profit of a validated incumbent, rather than a rounded solver objective.

The implication can be written P_j >= 1-(B+1)*(1-z_j), equivalently
sum_i(g_ji*x_i)>=(B+1)*z_j. The constant B+1 is valid because profits cannot
fall below -B. Integer profits make P_j>=1 exactly equivalent to strict
positivity. The objective lower bound -B is always valid; sum_j(P_j)=-B
gives the exact integer upper bound floor(-B/37). More strongly, if at least
r pockets have positive integer profit, then

    -B = sum_j(P_j) >= r + (37-r)*t,
    t <= floor((-B-r)/(37-r)).

For the five default targets these stronger upper bounds are respectively
-5, -6, -8, -11 and -18 chips. They are bounds, not assertions of feasibility.
If an exactly validated candidate attains such a bound, that coincidence
provides an analytical optimality proof within the stated integer scope.

For each target retain solver termination status and message, runtime, any
incumbent, objective and available dual bound/gap, selected bets and integer
stakes. Recompute all 37 profits using exact arithmetic after checking the
candidate's integrality, nonnegative allocation, total budget, active-bet cap
and positive-pocket requirement. Report profit distribution, positive/zero/loss
counts, worst profit, expected profit and expected profit per unit staked.
Candidate feasibility validated this way is exact. A solver's numerical
optimality or infeasibility report is a numerical certificate subject to its
tolerances, not formal verification or an independently checked exact proof.
A time-limited feasible incumbent establishes no optimality unless a separate
valid analytical bound certifies it. No incumbent at a time limit establishes
neither infeasibility nor a useful portfolio. Do not silently round an invalid
allocation into an accepted one.

Independent review must check the formulation, implication constant, objective
direction, solver status handling and exact post-validation. Compare a small
instance against independent exhaustive integer-allocation enumeration. Check
that every accepted portfolio satisfies sum_j(P_j)=-B. The existing five
disjoint six-line example and the covered-but-break-even example remain
settlement counterchecks; they do not certify this mixed-bet optimisation.

This is a finite integer-allocation problem. It neither enumerates continuous
stake allocations nor establishes a global optimum over arbitrary budgets,
unlimited distinct bets, all roulette variants or all venue products. Table
limits, bankroll/session dynamics, physical bias and real-world spin data are
excluded. The legal catalogue uses the convention documented in
[C1-001](COVERAGE_REGISTER.md). All probability calculations are exact under
the fair-wheel model; no Monte Carlo confidence intervals, seed or statistical
multiple-testing correction are applicable. No real-world positive edge is
established by these computations.
