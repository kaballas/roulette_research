# Validation plan (registered 12 October 2026)

## Phase 1: payout and fair-wheel baseline

Hypothesis: independent uniform pocket outcomes produce each bet's derived expected net profit per unit initially staked. The reference is exact arithmetic, not another Monte Carlo implementation. Tests enumerate all pockets for coverage sizes 1, 2, 3, 4, 6, 12 and 18; explicitly check the American five-number basket exception; and check French state transitions independently of the probability implementation.

The eight fixed Monte Carlo cases are the Cartesian product of four wheel rules (European, American, la partage, en prison) and two bets (red, straight-up zero). En prison uses independent *resolved wagers*: successive zeros retain the existing stake, and a later covered outcome returns it with zero profit. Every completed wager has one initial unit staked. This denominator differs from raw physical spins. Repeated-zero imprisonment is the selected rule, not a universal casino convention.

Before generating outcomes, calculate exact mean and variance and choose n = ceil(z² variance / 0.03²), with z = Phi^-1(1 - 0.01/(2 × 8)). Use analytic normal intervals estimate ± z sqrt(variance/n), with target half-width at most 0.03 units. Bonferroni adjusts eight simultaneous comparisons to nominal familywise coverage 99%. Normal approximation is asymptotic, not a finite-sample coverage guarantee. A miss is retained and investigated; no seed search, rerun-until-pass or post hoc widening. Seed 20261012 and the eight case ordering are fixed in the experiment entry point. Monte Carlo is corroborating evidence, not proof. A confidence interval containing the theoretical mean cannot prove independence or correctness by itself.

Implementation checks: deterministic seed replay, input validation, vectorised settlements against explicit outcome paths, prison stake held through zeros, and accounting identity ending bankroll = starting bankroll + realised profit with no unresolved liability at a session boundary. Session horizons count completed wagers; any imprisoned wager resolves fully before the next completed-wager count, so physical-spin counts are random and no artificial cash-out is used.

## Phase 2: finite-bankroll strategy comparison

Run only after exact payout tests and Phase 1 reconciliation pass. Compare flat stake and Martingale first, then the other requested staking and selection rules. Every requested stake must meet the table minimum, table maximum and available bankroll. Stop before a wager that cannot be funded; do not silently clip an unfundable progression or create debt. Prison resolution must not add turnover. A fresh stake counts once even when settlement requires several physical spins. Distinguish zero-bankroll ruin from inability to fund the next requested bet.

Use independent sessions with fixed seed and bounded completed-wager horizon (prison resolution may require additional physical spins). Record return on aggregate turnover (sum profit / sum initial stakes), mean session profit with confidence interval, mean turnover, drawdown, ruin, affordability/table-limit stopping, session win rate and tails. The target profit benchmark is −h times turnover for common-edge bets; baskets and mixed-edge bets require a stake-weighted benchmark. Reporting a high fraction of winning sessions is not evidence of an edge. Estimate uncertainty at the independent session level: spins within an adaptive session are not independent samples of final session profit. Treat interval estimates as approximate and use multiplicity adjustment for the fixed family of strategy checks. Record the chosen sample size before running experiments; do not stop on significance.

No external spins are present. These synthetic experiments are neither real-world data validation nor a chronological hold-out. Phase 3 would require wheel identity, timestamps, collection provenance, predeclared hypotheses and a sealed later sample; neither simulated fair-wheel agreement nor strategy selection supplies that evidence.

Independent Fraction arithmetic gives z = 3.2272184259631627 and these registered sample sizes:

| Wheel | Red | Straight zero |
| --- | ---: | ---: |
| European | 11,564 | 394,384 |
| American | 11,541 | 384,286 |
| La partage | 11,336 | 394,384 |
| En prison | 11,414 | 394,384 |

The en prison red variance is 5401/5476, whereas la partage red variance is 1341/1369. Their equal means −1/74 do not imply equal risk.

## Recorded Phase 1 registration deviation

The retained run uses per-case seeds 2026101200 through 2026101207 rather than the single seed 20261012 written above, and estimated rather than analytic variance for its displayed intervals. This was detected during independent review after the fixed run. Do not treat the run as exact adherence to the registration. The seeds and observed results are retained; no rerun or seed search is authorised by this discrepancy. The reviewer additionally checked the registered analytic-variance intervals on the retained outcomes: all eight still cover their analytical benchmarks. Estimated-variance interval widths may exceed the planning target slightly. See `docs/ADVERSARIAL_REVIEW.md` for the replay evidence.

## Fixed Phase 2 run registered before outcomes

Use 20,000 independent sessions per case, 100 completed wagers maximum, starting bankroll 100, table minimum 1 and maximum 64. Compare six progressions on red at base 1 and fixed flat six-number and red/zero portfolios at total bases 6 and 2 respectively. Run European and American rules for 16 cases. Use 48 simultaneous normal/delta-method intervals (mean profit, aggregate return ratio, and mean staking-identity residual for each case), Bonferroni family alpha 0.01. The same-spin portfolio components must share outcomes; generating independent component outcomes would distort risk.

The residual is session profit + h × session turnover. Its mean is zero under the theorem. For red, orthogonality of bounded martingale increments bounds its session variance by 100 × 64² × Var(unit profit). The 20,000 sessions suffice for a conservative residual half-width target 20 units with the registered simultaneous critical value; actual turnover should give smaller widths. Fixed portfolio stakes are substantially smaller. This is a bounded precision rationale, not a promise of power against every alternative or guaranteed normal coverage. No pilot outcome or significance stopping determines n. Win/ruin fractions and tails are descriptive, not extra uncorrected edge tests.

## Independent mathematical review

The validation author independently checked the ordinary-wager Bernoulli moments, basket exception, la partage moments, en prison geometric absorption law, expected prison spin count, and the adapted-stakes theorem in `docs/MATHEMATICS.md`. Fraction arithmetic independently matches all eight Phase 1 moment references. The theorem requires predictable nonnegative stakes, the stated conditional mean and integrable total turnover; bounded profits justify exchange of expectation and summation. Different-edge components need the weighted expectation benchmark. No derivation defect was found. This is ordinary mathematical review, not proof-assistant verification and not evidence of any real-world edge.
