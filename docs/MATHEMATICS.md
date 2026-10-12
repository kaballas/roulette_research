# Mathematical baseline

These are exact derivations under stated assumptions, checked with SymPy rational arithmetic. They are **proved** in the ordinary mathematical sense, not formally verified by a proof assistant. Simulations provide implementation checks, not proofs.

## Model and payout convention

Spins are independent and uniform over 37 European pockets or 38 American pockets. Identifier 0 is zero and identifier 37 is American double zero. French variants use the European pockets. Every reported profit excludes the returned original stake. A win paying 35 to 1 therefore has profit +35, a loss -1, and a returned stake profit 0.

`Bet` accepts standard coverage counts k in {1,2,3,4,6,12,18}, with net win b=36/k-1. Pocket uniqueness and wheel membership are checked. Physical table adjacency is not checked: arbitrary sets with these counts are synthetic wagers at the specified payout, not a claim that casinos offer them. The only five-pocket exception is the American basket {0,00,1,2,3}, paying 6 to 1.

French concessions apply to 18-pocket, 1-to-1 coverage excluding zeros. Other bets on French wheels settle as European bets. This is an explicit abstract model: actual venue rules would require separate verification before any real-world application.

## Exact ordinary-wager moments

For k winning pockets on an N-pocket wheel, X=b with probability k/N and X=-1 otherwise. Thus

    E[X] = (k(b+1)-N)/N
    Var(X) = (b+1)^2 k(N-k)/N^2.

Standard b+1=36/k gives E[X]=(36-N)/N, independent of coverage: -1/37 for European and -2/38=-1/19 for American. The American basket instead gives E[X]=(5*7-38)/38=-3/38.

| Wager | Mean unit profit | Variance |
| --- | --- | --- |
| European straight-up | -1/37 | 46656/1369 |
| American straight-up | -1/19 | 11988/361 |
| European even money | -1/37 | 1368/1369 |
| American even money | -1/19 | 360/361 |
| American basket | -3/38 | 8085/1444 |

## La partage

For qualifying even-money bets a zero loses half the stake immediately. The completed-wager law is P(X=1)=18/37, P(X=-1)=18/37, P(X=-1/2)=1/37. Consequently E[X]=-1/74 and Var(X)=1341/1369. Nonqualifying wagers keep the European moments.

## En prison and repeated zeros

After an initial zero a qualifying stake remains locked. Subsequent zeros keep it locked. The first nonzero outcome on the chosen side returns the original stake with no net winnings; the opposite side loses it. No additional stake is placed while waiting. This repeated-zero convention is part of the model, not a universal casino rule.

The eventual first nonzero side is equiprobable. Indeed the probability of eventual release on the chosen side is sum over j>=0 of (1/37)^j*(18/37)=1/2. Nonresolution has probability zero. The completed-wager law is therefore

    P(X=1) = 18/37,
    P(X=0) = (1/37)*(1/2) = 1/74,
    P(X=-1) = 18/37 + 1/74 = 1/2.

Hence E[X]=-1/74 and Var(X)=73/74-(1/74)^2=5401/5476. The expected spin count per initial wager is 1+(1/37)*(37/36)=37/36. Turnover counts the initial stake once, never again during imprisonment. A calendar-spin horizon with locked stakes must report liabilities or resolve them explicitly; treating them as losses or zero-valued completed wagers changes the model.

## Why adapted staking cannot remove the edge

Let F_(t-1) contain everything known before wager t, let S_t>=0 be measurable with respect to F_(t-1), and let X_t be unit profit with conditional expectation E[X_t|F_(t-1)]=-h. Choose S_t=0 after a stopping rule ends play. Finite bankroll, finite table limits and a bounded wager horizon give an integrable total stake automatically. More generally assume E[sum_t S_t]<infinity and uniformly bounded unit profit (as here).

Conditional expectation gives E[S_t X_t]=-h E[S_t]. Because |S_t X_t|<=35 S_t for the supported wagers, absolute integrability allows summing expectations:

    E[sum_t S_t X_t] = -h E[sum_t S_t].

Flat staking, Martingale and other predictable progressions satisfy this identity whenever those assumptions hold. Stopping after a win or at a bankroll/table constraint is already included through zero subsequent stakes. A high fraction of winning sessions can coexist with negative expected profit because rare large losses offset frequent small wins. The identity is an expectation relation, not a statement that every finite Monte Carlo sample has exactly that realised return ratio.

If bets have different edges, use E[X_t|F_(t-1)]=-h_t with predictable h_t, giving E[profit]=-E[sum_t h_t S_t]. All supported standard edges are positive. Correlated simultaneous bets change variance through covariance, but linearity still adds their expected profits and stakes. A positive expectation would require a changed assumption, such as a validated nonuniform wheel or different payouts, not merely a different progression.

For en prison, index t by completed wager starts; current spin-level conditional profits during an existing imprisonment need not have the original -1/74 mean. Complete outstanding wagers before applying the completed-wager identity. Without integrable total stakes, an idealised unlimited Martingale is outside this theorem; that omission does not establish a feasible profitable system.

## Fixed-budget board coverage optimisation

For a chosen standard European catalogue, let A[n,j] be the gross return
including returned stake on pocket n for one chip on bet j. Every column sums
to 36. With integer chips x[j]>=0 and total budget B, net profit is
P[n]=sum_j A[n,j]x[j]-B. Consequently sum_n P[n]=-B, so expected profit is
exactly -B/37 and return per chip is -1/37 for every feasible allocation.

Binary y[j] and constraints y[j]<=x[j]<=B*y[j], sum_j y[j]<=10 impose at
most ten occupied bet positions. Repeated chips on one position count as one
bet. Binary z[n] with sum_j A[n,j]x[j]>=(B+1)*z[n] and sum_n z[n]>=q impose
at least q strictly profitable pockets. This implication is exact for integer
chips: positive profit means at least one chip. It need not label every
profitable pocket with z=1; the final outcome vector supplies the actual count.

Maximise integer t subject to t<=P[n] for every pocket. This minimises the
worst possible loss at a fixed budget and target, rather than maximising EV,
which is identical across all feasible portfolios. Since profits sum to -B,
t<=floor(-B/37). Another necessary feasibility condition is q*(B+1)<=36*B,
because gross receipts are nonnegative and total gross receipts sum to 36*B.
Neither bound alone establishes that a legal ten-position portfolio exists.
For q<37 a stronger objective bound follows from at least q profits being
integers >=1 while the other profits are >=t:
-B>=q+(37-q)*t, hence t<=floor((-B-q)/(37-q)). A feasible allocation attaining
this bound proves optimality directly for the declared integer model. For
q=37 feasibility contradicts the negative sum of profits.

The finite integer budget and chip denomination are part of the problem.
Changing B changes the feasible stake ratios and the meaning of a one-chip
positive profit. A solver certificate concerns this declared model, not all
continuous stake allocations or all table rules. Exact rational re-settlement
certifies a returned portfolio's feasibility and expectation; numerical
mixed-integer bounds are separate evidence for optimality, not formal proof.

## Reproduction and falsifiable checks

`roulette.theory.distribution` enumerates ordinary settlement exactly and analytically resolves the en-prison absorbing state. `moments` computes rational mean and variance. Tests should enumerate every wheel/pocket and supported coverage, independently check the basket and French laws, and verify imprisoned zero/win/loss transitions. Fair-wheel Monte Carlo estimates must use declared sample sizes and uncertainty limits; an estimate outside its interval is evidence to investigate, not permission to tune the limit.
