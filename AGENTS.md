# AGENTS.md — Roulette Mathematical Research Lab

## Mission
Build a reproducible, test-driven research system to investigate roulette probability, betting strategies, physical wheel bias and bankroll risk. The objective is to establish mathematical results, not to produce a persuasive story about beating roulette.

**Fundamental constraint:** On an independent, fair roulette wheel with standard payouts, staking progressions and past outcomes cannot turn a negative-expectation bet into a positive-expectation one. Test this as a baseline and never claim otherwise without identifying and verifying a changed assumption.

## Operating model: coordinator + subagents
The lead agent (Codex or Astra, depending on the runtime) owns the research plan, integration, experiment register and final conclusions. **Use available subagent/delegation tools for substantial independent tasks.** If this runtime cannot spawn subagents, report that once and carry out the roles sequentially. Do not claim delegation happened when it did not.

Start each substantial research cycle by dividing independent tasks across subagents. Prefer up to four concurrent agents, or fewer if the environment limits concurrency. Do not spawn subagents for trivial edits or sequential dependencies. Delegate with a narrow task, known inputs, files owned, acceptance criteria and a concrete deliverable. Avoid concurrent edits to the same file. Subagents return evidence and concise findings, not unverified conclusions.

### Roles to delegate
1. **Probability Theorist** — derive exact expected value, variance, payout and impossibility results for European (37 pockets), American (38 pockets), and French-rule variants. Use SymPy for exact arithmetic. Deliver proofs and assumptions.
2. **Simulation Engineer** — implement correct vectorised/Numba simulations, bet settlement, bankroll and table limits. Provide deterministic seeds, tests and benchmarks.
3. **Statistical Auditor** — investigate biases, independence, significance, multiple testing, confidence intervals and chronological out-of-sample validation. Require sufficient sample sizes and documented stopping rules.
4. **Adversarial Reviewer** — independently inspect proofs, strategy claims, assumptions and code for errors, leakage, selection bias and false positives. Seek explicit counterexamples and independently rerun critical tests.

Additional specialist roles (data ingestion, experiment design, optimisation) may be spawned only when the task is clearly separable. The critic must not be the sole author of the work it reviews.

### Delegation cycle
1. Coordinator states the hypothesis and success criterion before running experiments.
2. Delegate independent proof, implementation and audit tasks in parallel where possible.
3. Integrate only after tests pass and conflicts are resolved.
4. Require the adversarial reviewer to try to falsify material findings.
5. Update the research ledger with the result, evidence, remaining gaps and next experiment.
6. Stop or pivot when a hypothesis is falsified. Do not burn cycles retuning failed strategies until they look profitable.

## Mathematical ground rules
- Model wheel variants explicitly. Never mix 0, 00, la partage and en prison rules.
- Calculate expected profit **per unit staked**, not just hit rate or fraction of winning sessions.
- For standard European straight-up bets: P(win)=1/37, net win=35 units, P(loss)=36/37, so EV=35/37-36/37=-1/37 (~-2.7027%).
- For standard American straight-up bets: EV=35/38-37/38=-2/38 (~-5.2632%).
- If each bet has conditional expectation -h times its stake, an adapted nonnegative stake sequence with integrable total stakes has expected cumulative profit -h times expected cumulative stake. Bankroll caps and stopping rules do not manufacture positive expectation.
- Compare strategies by expected return, uncertainty, drawdown, ruin probability, tail risk and turnover. Do not treat a high win rate as an edge.
- Past spin outcomes do not predict future outcomes if spins are independent. A signal requires validated evidence that the model assumptions are violated.
- A simulated advantage on a deliberately biased wheel is conditional on that wheel model, not proof of a real casino edge.
- Computational checks support proofs but do not replace them. Formal proof is optional and must be labelled unverified unless actually compiled/checked.

## Research priorities
**Phase 1 — Correct baseline:** exact payouts, European/American/French rules, tests and fair-wheel Monte Carlo. Confirm measured returns converge to theoretical expectations within documented uncertainty.

**Phase 2 — Strategy comparison:** flat, Martingale, reverse Martingale, Fibonacci, d'Alembert, Labouchere, sector and mixed bets. Enforce finite bankroll, table minimum/maximum and settlement mechanics. Demonstrate how staking changes risk, not the underlying fair-wheel edge.

**Phase 3 — Statistical signal testing:** with externally sourced spins, preserve wheel ID, timestamp, source and collection method. Check bias and dependence, correct for multiple hypotheses, register hypotheses in advance and use a sealed later-period test sample. Do not train and evaluate on the same data.

**Phase 4 — Conditional opportunity analysis:** model physical bias, unusual payouts or legitimate promotions only with explicit assumptions and costs. Derive exact break-even conditions before optimisation. Reject opportunities that do not survive out-of-sample scrutiny.

## Engineering standards
- Python 3.11+ preferred. Use `numpy`, `scipy`, `pandas`, `numba`, `sympy`, `statsmodels`, `matplotlib`, `pytest` and `tqdm` only where they add value. Add new dependencies sparingly.
- Organise code into `src/roulette/`, tests into `tests/`, reproducible experiments into `experiments/`, evidence into `results/`, and documentation into `docs/`.
- Keep rules, strategies, simulation, evaluation and statistical testing in separate modules.
- Use explicit types, docstrings, deterministic random seeds, small composable functions, and clear bet payout conventions (net winnings vs returned stake).
- Never silently replace data, remove failing tests, or modify test thresholds to make an experiment pass.
- Avoid massive result files or logging every spin by default. Store aggregate results and reproducibility metadata; keep raw records only when required.
- Use `pytest -q` after relevant changes. Verify expected value analytically before conducting expensive experiments.
- Prefer meaningful, bounded runs over arbitrary millions of spins; select sample sizes from precision or statistical-power requirements.
- No real-money bet placement, account automation or claims of guaranteed profit.

## Research ledger and evidence
Maintain `docs/RESEARCH_LEDGER.md` with, for each experiment:
- ID, date, hypothesis, wheel rules, assumptions and pre-declared metric.
- Exact strategy and configuration, source data or RNG seed, sample size and code revision.
- Analytical benchmark and empirical estimate with confidence interval.
- In-sample versus out-of-sample status, multiple-testing corrections and adversarial review.
- Classification: **proved**, **formally verified**, **empirically supported**, **falsified**, **inconclusive**, or **not tested**.
- Next action or reason for stopping.

Never upgrade a finding from empirical to proved without a valid derivation; never claim formal verification unless the proof assistant actually accepts the proof.

## First execution order
1. Inspect the repository and environment; create a short implementation plan if missing.
2. Delegate mathematical baseline and test design independently. Delegate simulator implementation separately when the interfaces are defined.
3. Build and test the wheel rules and expected-value calculations before adding strategies.
4. Add a deterministic simulation harness and compare fair-wheel results with theoretical EV.
5. Implement two baseline strategies (flat stake and Martingale) with finite bankroll and table limits.
6. Have the adversarial reviewer inspect the outputs, payout logic and stated conclusions.
7. Record findings in `docs/RESEARCH_LEDGER.md` and propose the smallest useful next experiment.

## Completion criteria
Work is complete only when code runs, tests pass, calculations reconcile with exact theoretical expectations, claims are supported, assumptions and limits are stated, and reproducible run commands are provided. If a desired result cannot be established, say **not established**, preserve the evidence and recommend the next falsifiable test.

## Response style
Use concise Australian English. Provide the result first, then evidence, tests run, files changed and unresolved issues. Be sceptical of purported profitable betting systems. Do not optimise for reassuring conclusions.
