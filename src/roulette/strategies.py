"""Predictable staking progressions and fixed correlated bet portfolios."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from roulette.rules import Bet, RED, STRAIGHT_ZERO, straight


@dataclass(frozen=True)
class Portfolio:
    """Same-spin component bets; weights are fractions of total initial stake."""
    name: str
    components: tuple[tuple[Bet, float], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.components, tuple) or not self.components:
            raise ValueError("nonempty immutable components required")
        if any(not isinstance(b, Bet) or not math.isfinite(w) or w <= 0
               for b, w in self.components):
            raise ValueError("positive finite Bet weights required")
        total = sum(w for _, w in self.components)
        if not math.isclose(total, 1, abs_tol=1e-12, rel_tol=0):
            raise ValueError("weights must sum to one")
        object.__setattr__(self, "components", tuple((b, w / total) for b, w in self.components))


# Six adjacent pockets on the European physical wheel; the same fixed number
# set is used on American wheels, where it does not describe an adjacent sector.
SECTOR = Portfolio("six_number_portfolio", tuple((straight(n), 1 / 6) for n in (32, 15, 19, 4, 21, 2)))
MIXED = Portfolio("red_and_zero", ((RED, .5), (STRAIGHT_ZERO, .5)))

NAMES = ("flat", "martingale", "reverse_martingale", "fibonacci", "dalembert", "labouchere")


class Progression:
    """Independent per-session states; zero-profit releases leave state unchanged.

    Fractional losses advance the loss step. Labouchere appends the full
    requested stake, so its cancellation interpretation assumes unit wins/losses.
    Experiment comparisons use standard even-money bets for progressions.
    """
    def __init__(self, name: str, sessions: int, base: float = 1) -> None:
        if name not in NAMES:
            raise ValueError(f"unknown strategy {name!r}")
        if type(sessions) is not int or sessions < 1 or not math.isfinite(base) or base <= 0:
            raise ValueError("positive session count and finite base required")
        self.name, self.base = name, float(base)
        self.level = np.ones(sessions, dtype=float)
        self.index = np.zeros(sessions, dtype=int)
        self.sequences = [[1., 2., 3.] for _ in range(sessions)] if name == "labouchere" else []
        fibonacci = [1., 1.]
        for _ in range(78):
            fibonacci.append(fibonacci[-1] + fibonacci[-2])
        self.fibonacci = np.array(fibonacci)

    def stakes(self) -> np.ndarray:
        """Requested total stakes before the next outcomes are observed."""
        if self.name == "labouchere":
            return self.base * np.array([s[0] + s[-1] if len(s) > 1 else s[0] for s in self.sequences])
        if self.name == "fibonacci":
            needed = int(self.index.max())
            if needed >= len(self.fibonacci):
                terms = self.fibonacci.tolist()
                while len(terms) <= needed:
                    terms.append(terms[-1] + terms[-2])
                self.fibonacci = np.asarray(terms)
            return self.base * self.fibonacci[self.index]
        return self.base * self.level.copy()

    def update(self, indices: np.ndarray, unit_profit: np.ndarray) -> None:
        """Advance only the sessions whose completed outcomes are supplied."""
        indices = np.asarray(indices, dtype=int)
        values = np.asarray(unit_profit, dtype=float)
        if indices.ndim != 1 or indices.shape != values.shape or not np.all(np.isfinite(values)):
            raise ValueError("matching finite outcome vectors required")
        if np.any(indices < 0) or np.any(indices >= len(self.level)) or len(np.unique(indices)) != len(indices):
            raise ValueError("unique valid session indices required")
        win, loss = indices[values > 0], indices[values < 0]
        if self.name == "martingale":
            self.level[win] = 1
            self.level[loss] *= 2
        elif self.name == "reverse_martingale":
            self.index[loss] = 0
            self.index[win] = (self.index[win] + 1) % 3
            self.level[indices] = 2. ** self.index[indices]
        elif self.name == "fibonacci":
            self.index[win] = np.maximum(0, self.index[win] - 2)
            self.index[loss] += 1
        elif self.name == "dalembert":
            self.level[win] = np.maximum(1, self.level[win] - 1)
            self.level[loss] += 1
        elif self.name == "labouchere":
            for i in win:
                seq = self.sequences[i]
                self.sequences[i] = seq[1:-1] if len(seq) > 2 else [1., 2., 3.]
            for i in loss:
                seq = self.sequences[i]
                seq.append(seq[0] + seq[-1] if len(seq) > 1 else seq[0])


def make_strategy(name: str, sessions: int, base: float = 1) -> Progression:
    """Construct fresh session states for one simulation run."""
    return Progression(name, sessions, base)
