# P2-001 registered configuration

Registered before the primary comparison run, 12 October 2026.
Phase 1 passed 68 tests and all eight planned Monte Carlo comparisons.

Hypothesis: staking changes session risk, while expected profit remains
minus the common house edge times expected turnover. Primary reconciliation
metric is the mean session residual `profit + h * turnover`, benchmark zero.
Secondary metrics are mean session profit and ratio of aggregate profit to
aggregate turnover, benchmark return −1/37 (European) or −1/19 (American).

Six progressions on red: flat, Martingale, reverse Martingale (reset after three
consecutive wins), Fibonacci (up one step on loss, down two on win), d'Alembert
(up one unit on loss, down one on win, minimum one), Labouchere (initial list
1,2,3, stake sum of ends or single remaining entry, remove ends on win, append
stake on loss, restart list after cancellation). Start base stake one unit.
Additional flat allocations: six straight-up bets on 32,15,19,4,21,2 at one unit
each, and one unit each on red and zero. Those six numbers are adjacent only on
the European wheel; the American comparison uses the same fixed number set.
Components share the same spin, never independent draws.

Sixteen cases: eight configurations on each of European and American wheels.
20,000 independent sessions each, initial bankroll 100 units, horizon 100
completed wagers, component minimum 1, component and total maximum 64. Stop
before illegal or unaffordable requested stakes without clipping. Distinguish
zero bankroll from a positive bankroll that cannot fund the next stake. No
profit target. Drawdown uses settled bankroll. No unresolved prison liability
is relevant to these standard-wheel experiments; French session mechanics are
tested separately. Fractional units are allowed by the API.

Seeds are 2026101300 + case index, European cases first, in the order above.
All 48 mean-profit, aggregate-ratio and residual intervals use asymptotic
normal 99% familywise intervals, Bonferroni corrected across 48. Ratio intervals
use session-level delta-method covariance; session win/ruin rates and tail
summaries are descriptive estimates. No significance-based stopping.

Precision justification: for red, residual martingale variance is bounded by
100 × 64² × Var(unit profit) < 409,600. With 20,000 sessions and the
48-comparison critical value this gives a normal planning half-width below
20 bankroll units. The flat sector/mixed configurations have smaller bounds
because their stakes are fixed at 6/2; exact same-spin variances can be
enumerated. This conservative bound sets sample count; observed precision is
reported, not promised. The normal approximation is not a finite-sample
guarantee, and intervals containing zero do not prove the identity.

Engineering timing smoke runs were performed by the simulator author using
seed 20261012. They are exploratory and not primary evidence; they did not
change this configuration, sample count, hypotheses or primary seeds. No
optimisation or favourable-seed selection is permitted.
