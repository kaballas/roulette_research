# Research ledger

All entries dated 12 October 2026. No external spin data, training sample or real-money execution is involved. Source revisions are identified by SHA-256 manifests embedded in each JSON artefact; no Git repository was present. Original run artefacts are preserved. These findings are conditional on independent uniform pockets and the stated payout model.

## M1-001 — exact baseline

**Hypothesis:** each standard payout has a negative unit-stake expectation, and predictable integrable staking cannot remove it. **Metric:** exact expected net profit and variance. European 37-pocket, American 38-pocket and explicitly modelled French rules; en prison repeated zeros hold. No sample, RNG seed, interval or multiple-testing correction applies to exact derivations.

**Evidence:** `src/roulette/rules.py`, `src/roulette/theory.py`, `docs/MATHEMATICS.md`, independent Fraction-based tests and the statistical auditor’s proof review. European standard EV −1/37; American standard EV −1/19; American five-number basket −3/38; qualifying French even-money wagers −1/74. Other French bets retain −1/37. Both French concessions share a mean but have different variances.

**Classification: proved** under the documented assumptions; **not formally verified**. The conditioning and integrability argument gives E[profit] = −h E[turnover]. Bounded session horizons and stake caps establish integrability. Weak-law convergence also follows for independent completed unit wagers: Var(sample mean) = Var(X)/n and Chebyshev bounds the probability of error at least epsilon by Var(X)/(n epsilon²), which tends to zero. Finite empirical errors need not decrease monotonically.

**Adversarial review:** the statistical auditor independently checked the derivations; the proof author independently reviewed other agents’ simulator and statistics, not their own proofs. Next action: corroborate settlement and sample means computationally (P1-001).

## P1-001 — fair-wheel completed wagers

**Hypothesis and metric:** fair-wheel mean net profit per initial unit staked agrees with the exact EV. Eight fixed cases; sample sizes chosen from exact variance for a 0.03-unit normal planning half-width. Fixed stopping after n completed wagers; no retuning. Independent uniform PCG64 outcomes. Seeds 2026101200–2026101207 in the order below. En prison resolution uses actual repeated pocket draws, one initial stake only.

**Evidence:** `results/baseline.json`; run `PYTHONPATH=src python experiments/baseline.py --output /tmp/roulette-baseline.json` with a fresh path. Code revision and package versions are embedded in metadata. Intervals below are sample-standard-error normal intervals, Bonferroni corrected across eight cases for nominal asymptotic 99% familywise coverage.

| Wheel | Bet | n | Exact EV | Estimate | Interval |
| --- | --- | ---: | ---: | ---: | --- |
| european | red | 11,564 | -1/37 | -0.021792 | [-0.051797, 0.008213] |
| european | straight_0 | 394,384 | -1/37 | -0.029951 | [-0.059907, 0.000006] |
| american | red | 11,541 | -1/19 | -0.057967 | [-0.087958, -0.027976] |
| american | straight_0 | 384,286 | -1/19 | -0.029848 | [-0.060196, 0.000501] |
| la_partage | red | 11,336 | -1/74 | -0.018834 | [-0.048829, 0.011162] |
| la_partage | straight_0 | 394,384 | -1/37 | -0.026299 | [-0.056310, 0.003712] |
| en_prison | red | 11,414 | -1/74 | -0.005257 | [-0.035250, 0.024736] |
| en_prison | straight_0 | 394,384 | -1/37 | -0.027212 | [-0.057209, 0.002785] |

**Registration deviation:** the independent validation plan specified exact-variance intervals and seed 20261012, whereas the coordinator’s pre-run entry point specified per-case seeds 2026101200+i and used estimated standard errors. The discrepancy was discovered during review after the first run, and is retained here. The reviewer independently replayed every recorded seed and confirmed that all eight cases also pass the originally described exact-variance intervals. The 0.03 half-width is a planning target; some estimated intervals are slightly wider. No evidence was replaced, no seed was searched and no thresholds were widened.

**Classification: empirically supported.** All eight intervals include their exact EV. This is corroboration of the implementation, not a proof of independence, exact coverage, or a real casino edge. Some intervals include zero; the exact negative expectation is established analytically, not by those finite samples. Normal coverage is asymptotic. All data are synthetic; neither in-sample training nor chronological out-of-sample evaluation applies. Next action: finite-bankroll comparison after the analytical/test gate (P2-001).

## P2-001 — finite-bankroll strategy comparison

**Hypothesis:** staking changes risk but leaves E[profit + h × turnover] = 0. **Predeclared metrics:** residual mean against zero, aggregate profit/stake ratio against −h, and mean session profit. Exact configuration and sample-size rationale: `docs/PHASE2_REGISTER.md`. 20,000 independent sessions per case, 100 completed-wager cap, bankroll 100, component minimum 1, component and total maximum 64. Six progressions on red use base 1 (Labouchere starts with requested stake 4); flat six-number and red/zero portfolios use total stakes 6 and 2. Component bets settle on the same spin. No clipping, no profit target, no tuning.

**Evidence:** `results/strategies.json`; run `PYTHONPATH=src python experiments/strategies.py --output /tmp/roulette-strategies.json`. Seeds 2026101300–2026101315, ordered as in the table. Code revision and versions are embedded in metadata. Forty-eight intervals are Bonferroni corrected for nominal asymptotic 99% familywise coverage: session profit, session-cluster delta-method aggregate return, and residual for each case. Win/ruin/stopping/tail rates are descriptive estimates. Engineering timing runs used a separate exploratory seed, did not change the registered settings and are not primary evidence.

| Wheel | Strategy / selection | Mean profit [interval] | Return/stake | Winning sessions | Ruin | Cannot fund next | Mean max drawdown |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| european | flat | -2.784 [-3.047, -2.522] | -2.784% | 35.12% | 0.00% | 0.00% | 12.808 |
| european | martingale | -6.488 [-7.946, -5.029] | -2.805% | 48.91% | 0.56% | 49.85% | 54.574 |
| european | reverse_martingale | -4.661 [-5.174, -4.147] | -2.763% | 38.67% | 0.00% | 0.00% | 24.608 |
| european | fibonacci | -5.480 [-6.560, -4.399] | -2.567% | 74.15% | 0.00% | 22.72% | 39.075 |
| european | dalembert | -12.356 [-13.917, -10.795] | -2.666% | 54.91% | 1.29% | 29.08% | 66.300 |
| european | labouchere | -15.162 [-17.360, -12.963] | -2.730% | 38.57% | 1.52% | 58.07% | 93.588 |
| european | six_number_portfolio | -11.272 [-14.135, -8.410] | -2.576% | 38.63% | 0.00% | 49.18% | 119.933 |
| european | red_and_zero | -5.379 [-6.875, -3.884] | -2.699% | 43.72% | 4.24% | 0.00% | 58.832 |
| american | flat | -5.248 [-5.510, -4.986] | -5.248% | 27.02% | 0.00% | 0.00% | 14.027 |
| american | martingale | -12.311 [-13.749, -10.874] | -5.313% | 44.09% | 0.72% | 54.48% | 57.122 |
| american | reverse_martingale | -8.907 [-9.412, -8.401] | -5.340% | 30.05% | 0.00% | 0.00% | 26.447 |
| american | fibonacci | -11.993 [-13.136, -10.850] | -5.374% | 68.07% | 0.00% | 27.79% | 43.597 |
| american | dalembert | -25.129 [-26.698, -23.560] | -5.306% | 45.34% | 1.52% | 37.08% | 72.708 |
| american | labouchere | -28.477 [-30.523, -26.431] | -5.292% | 31.78% | 1.59% | 64.86% | 96.865 |
| american | six_number_portfolio | -22.115 [-24.802, -19.429] | -5.246% | 34.45% | 0.00% | 53.40% | 120.393 |
| american | red_and_zero | -9.944 [-11.430, -8.459] | -4.997% | 39.62% | 5.59% | 0.00% | 60.980 |

**Results:** all sixteen aggregate-return intervals contain their theoretical benchmark (European −2.7027%, American −5.2632%); all sixteen residual intervals contain zero; all sixteen mean-profit intervals are negative. Full intervals, turnover, table-limit stops, fifth percentiles and lower-tail means are stored in the JSON. Positive-funds inability to stake is distinct from ruin, and can coincide with a table-limit flag. A drawdown may exceed initial bankroll after prior winnings. Lower-tail means include all observations tied at the fifth percentile, so they are not an exact fixed-mass expected-shortfall estimator.

European Fibonacci won 74.15% of sessions yet averaged −5.480 units; its lower-tail mean was −86.491. Flat red averaged −2.784 with mean drawdown 12.808; Martingale averaged −6.488 with drawdown 54.574 and much larger turnover. These compare the registered configurations, not matched-turnover causal effects or a universal ranking of strategies. Larger losses in units often reflect larger turnover. No pairwise strategy-ranking hypothesis was tested.

**Classification: empirically supported** for finite Monte Carlo agreement and the stated risk estimates; **proved** separately for the expectation identity under the model. The claim that a staking progression makes fair-wheel expectation positive is **falsified analytically** under these assumptions. No physical bias, unusual payouts, promotions, real-world edge or out-of-sample signal has been established. French session mechanics are deterministically tested but French portfolio combinations are not implemented; the registered strategy comparison deliberately uses standard European/American rules.

**Adversarial review and fixes:** independent tests found and preserved a Fibonacci lookup saturation counterexample; dynamic extension fixed it, including runs beyond the original lookup. Portfolio settlement was changed to returns minus initial stake so an all-loss allocation is exactly −1; accepted near-one weights are normalised. Evaluation rejects malformed session vectors and invalid house edges. See `docs/ADVERSARIAL_REVIEW.md` for independent replay evidence and limitations.

**Next smallest useful experiment:** compare flat and Martingale under a preregistered equal-turnover exposure budget to separate turnover from risk more directly. Do not retune these strategies to chase positive returns. Phase 3 remains **not tested** and requires a specified external source, wheel IDs, timestamps, collection method, multiple-testing plan and sealed chronological hold-out.

## Verification

Final test and deterministic replay evidence is recorded in `results/verification.json`. All required rules, strategies, limits and experiment entry points are exercised. The original aggregates remain immutable; final replay checks compare their numerical content against current source. No proof assistant was used.

### README and verifier maintenance review — 12 October 2026

This review corrects documentation and evidence validation; it introduces no new
research experiment or statistical claim. README wording now distinguishes exact
derivations from Monte Carlo corroboration, identifies the eight configurations
and selected French convention, and aligns the next experiment with P2-001.

The reproduction commands now pass their generated files explicitly to the
verifier using `--baseline` and `--strategies`. Previously the verifier always
read the repository aggregates. It also accepted empty case lists and relied on
assertions disabled by `python -O`. Explicit validation now requires the complete
case sets and checks numerical reconciliation independently of optimisation.
Input paths and hashes identify the evidence actually replayed. Regression tests
are in `tests/test_verify.py`; a separate maintenance replay is retained in
`results/readme-review-verification.json`. The original result files are preserved.

## C1-001 — exact board coverage enumeration

**Date:** 12 October 2026. **Hypothesis:** frequent positive-profit spins coexist
with negative expected return. **Predeclared metric:** number of pockets with
strictly positive total net profit, after deducting every chip. Registration:
`docs/COVERAGE_REGISTER.md`. Standard fair European wheel, 37 equally likely
pockets; one chip per distinct selected bet. No bankroll or table-limit model,
French concession, external data, seed or hold-out sample applies.

**Configuration and evidence:** exhaust all 2,046 subsets of one to ten of the
eleven six-lines. `results/coverage-six-lines.json` records exact outcome vectors,
distributions, deterministic representatives, threshold counts, dependency
versions and SHA-256 source revision. Reproduce with a fresh output path:
`PYTHONPATH=src python experiments/coverage.py --output /tmp/roulette-coverage.json`.
No sampling interval or multiple-testing correction is needed for finite exact
enumeration. Maximum profitable pocket counts for one through ten bets are
6, 12, 18, 24, 30, 15, 18, 21, 24 and 27 respectively.

| Minimum profitable outcomes | Required pockets | Qualifying combinations |
| --- | ---: | ---: |
| 70% | 26 | 163 |
| 75% | 28 | 21 |
| 80% | 30 | 21 |

All 21 combinations reaching 80% use five disjoint six-lines: profit +1 on
30 pockets and −5 on seven, exact expectation −5/37 per five units staked.
Scaling each chip to ten gives +10/−50 and expectation −50/37. Covering 36
pockets using six disjoint six-lines instead gives zero profit on those pockets
and loses six units on zero; none of the outcomes is profitable.

**Analytical benchmark:** every catalogue bet has total profit −1 across its
37 equally likely outcomes. Linearity therefore gives expectation −k/37 for
k unit chips, or −1/37 per unit staked, regardless of overlap. For five equal
six-lines, a single hit returns six chips against five staked, so positive
outcomes equal their union; its size is at most 30, attained by disjoint lines.
**Classification: proved** for these exact identities and the five-line bound;
the remaining finite-search counts are **empirically supported by exhaustive
computation and independent replication**, not proof-assistant verification.

**Scope limitation:** the full 157-bet catalogue requires 2,005,902,398,704,387
subsets up to ten bets. `results/coverage-full-catalogue-preflight.json` records
that search as **not tested**, rejected before enumeration by the one-million
combination budget. Unequal stake optimisation, announced sector wagers and
American layouts are also not tested. No universal optimal coverage system or
real-world advantage is established.

**Adversarial review:** a separate agent independently reconstructed layout
geometry and enumerated all 2,046 portfolios without using the production search.
Every outcome vector and threshold total agreed. The reviewer also independently
ran all 26 new coverage tests; the integrated suite passed **188 tests**. Original
baseline and strategy evidence was preserved. **Next action:** if a concrete
viral allocation is supplied, evaluate its exact outcome vector; for broader
search, preregister a finite chip budget or an optimisation formulation before
claiming completeness. Do not tune stake allocation to manufacture positive EV.

## C2-001 — mixed integer board coverage, 12 October 2026

Registered in `docs/COVERAGE_OPTIMISATION_REGISTER.md` before execution.
Hypothesis: mixed legal bets with unequal stakes can improve worst-case loss
relative to a particular equal-chip portfolio at a required profitable-spin
frequency, while expected return remains negative. The registered metric is
maximum worst-pocket net profit, with at least 26/28/30/32/34 strictly positive
outcomes. Fair standard European wheel; all 157 catalogue bets; exactly 20
integer chips; at most ten occupied positions; ten solver seconds per target.
No French concessions, table limits, session dynamics or continuous allocations.

Reproduce with a fresh output path:

```sh
PYTHONPATH=src python experiments/optimise_coverage.py \
  --output /tmp/roulette-coverage-optimisation.json
```

Evidence: `results/coverage-optimisation-20chips.json` retains all five raw
solver outcomes, messages, runtimes, available numerical bounds/gaps, exact
stake allocations, all 37 profits and complete distributions. Versions,
source SHA-256 hashes and the registration hash identify the run; no Git
revision exists. `results/coverage-optimisation-audit.json` records independent
scalar settlement and reuse of feasible witnesses across targets. Every source
manifest hash matched the current source at audit. No seed, sample size,
confidence interval, in/out-of-sample split or multiple-testing adjustment is
applicable to deterministic outcome enumeration and optimisation.

Every solve reached its time limit. No optimum was established. The following
table combines feasible allocations across targets; a missing incumbent in
one solve does not override a witness found by another.

| Required positive frequency | Positive pockets required | Exact lower bound on worst loss | Best retained feasible worst loss |
| --- | ---: | ---: | ---: |
| 70% | 26 | 5 chips | 15 chips |
| 75% | 28 | 6 chips | 15 chips |
| 80% | 30 | 8 chips | 18 chips |
| 85% | 32 | 11 chips | Not established |
| 90% | 34 | 18 chips | Not established |

The solve targeting 70% returned a four-position portfolio: one chip on
the zero trio (0,1,2), seven on first dozen, one on low and eleven on high.
It profits on 30 pockets (81.08%): net -18 on six pockets, -8 on one, +2 on
18, +3 on ten and +15 on two. This also proves the 80% target feasible.
The solve targeting 75% returned a seven-position portfolio profitable on
29 pockets, with worst loss 15 chips. Its full allocation is retained in the
raw evidence. At the same 20-chip outlay, five disjoint equal six-lines lose
20 chips in the worst case. The retained 80% witness reduces that particular
worst loss by two chips; this is not a global optimality claim.

Analytical benchmark: sum of the 37 profits is exactly -20, so expectation
is -20/37 chips and return per chip is -1/37 for every feasible allocation.
At least r positive integer profits imply worst profit
<=floor((-20-r)/(37-r)), yielding the table's lower bounds on worst loss.
**Classification: proved** for these identities, bounds and exactly settled
candidate feasibility; **inconclusive** for all five global optima and for
85%/90% feasibility. No formal verification, universal best allocation or
positive edge is claimed.

Independent adversarial review checked the MILP formulation, exact implication
constant, numerical certificate handling and ten small mixed-bet instances
against a separate exhaustive integer-allocation oracle. The integrated suite
passed **232 tests**, including 44 new optimiser/CLI tests. Original evidence
was preserved. Coverage optimisation now takes priority over the earlier
equal-turnover Martingale proposal. Next useful experiment: preregister a
stronger formulation or explicitly longer solver budget for the unresolved
20-chip frontier, retaining these results as the original bounded run.
