# C1-001 — board coverage enumeration

Registered before the enumeration run, 12 October 2026.

Hypothesis: a high fraction of positive-profit spins can coexist with negative
expected profit. Count positive net profit after deducting every component stake,
not just outcomes covered by a chip. For standard European payouts, linearity
gives expected net profit = minus total stake / 37, including overlapping bets.

The first exhaustive experiment uses the eleven six-lines on the standard
three-column, twelve-street layout, distinct selections of one to ten bets,
one unit on each. Enumerate every subset in this scope, without stopping on a
favourable result. The total is sum(C(11,k), k=1..10) = 2,046. Outcomes 0–36
are independent uniform pockets; no French concessions or physical bias apply.

For each bet count, report the maximum number of strictly profitable pockets,
a deterministic representative, covered/positive/zero/negative counts and profit
distribution. Also count combinations reaching at least 70%, 75% and 80%
strictly profitable outcomes: respectively 26, 28 and 30 of 37. These are exact
finite outcome counts, requiring no seed, confidence interval or multiple-testing
correction. Selection within this enumerated model establishes no real-world edge.

The catalogue also models standard straight-ups, adjacent splits, streets,
corners, dozens, columns and even-money bets, including the single-zero split,
trio and first-four conventions. These payout and layout definitions follow
[Crown's published roulette rules](https://www.crownmelbourne.com.au/getsydmedia/379b919b-5cef-41f5-9642-e78c1fabccea/crown-melbourne-gaming-roulette-rules.pdf?ext=.pdf).
Availability and limits depend on the venue. This is a selected European model,
not a representation of every roulette product offered by Crown.

Full-catalogue enumeration up to ten bets is not promised: compute its size
first and reject runs exceeding the explicit combination budget. No truncation
may be labelled exhaustive. Unequal allocations, repeated chip placements,
American layouts, announced sector wagers, finite-session risk and table limits
are outside this first search. The exact evaluator can separately inspect
specified positive stake allocations. No optimisation of a failed expectation
claim is intended; useful findings describe the hit-rate/loss trade-off.

Independent review must check geometry, payout returns including original stake,
overlap, strict positivity, completeness and search limits. The reference example
uses six-lines 1–6, 7–12, 13–18, 19–24, 25–30 at ten units each: profit +10 on
30 pockets, −50 on seven, exact mean −50/37. Six disjoint equal six-lines instead
return the total stake on covered numbers: covering 36 pockets does not imply
any profitable outcome.
