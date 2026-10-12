"""Unit-stake net settlement; pocket 37 denotes American double zero."""

from dataclasses import dataclass
from enum import Enum


class Wheel(str, Enum):
    EUROPEAN = "european"
    AMERICAN = "american"
    LA_PARTAGE = "la_partage"
    EN_PRISON = "en_prison"


def pockets(wheel: Wheel) -> tuple[int, ...]:
    """Return pocket identifiers, requiring an explicit supported wheel."""
    wheel = Wheel(wheel)
    return tuple(range(38 if wheel == Wheel.AMERICAN else 37))


@dataclass(frozen=True)
class Bet:
    """Covered pockets and net winning profit for one unit of initial stake.

    Standard payout counts are enforced, but physical table adjacency is not:
    synthetic sets with a standard count are useful mathematical portfolios.
    """

    name: str
    numbers: tuple[int, ...]
    payout: int

    def __post_init__(self) -> None:
        if not isinstance(self.numbers, tuple):
            raise ValueError("numbers must be an immutable tuple")
        if any(type(n) is not int or not 0 <= n <= 37 for n in self.numbers):
            raise ValueError("pockets must be integers from 0 to 37")
        if len(set(self.numbers)) != len(self.numbers):
            raise ValueError("covered pockets must be unique")
        count = len(self.numbers)
        basket = set(self.numbers) == {0, 37, 1, 2, 3}
        expected = 6 if basket else (36 // count - 1 if count in {1, 2, 3, 4, 6, 12, 18} else None)
        if type(self.payout) is not int or self.payout != expected:
            raise ValueError("unsupported coverage or payout")


RED = Bet("red", (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36), 1)
STRAIGHT_ZERO = Bet("straight_0", (0,), 35)
AMERICAN_BASKET = Bet("american_basket", (0, 37, 1, 2, 3), 6)


def straight(number: int) -> Bet:
    """Construct a straight-up bet (37 means double zero)."""
    return Bet(f"straight_{number}", (number,), 35)


def validate_bet(wheel: Wheel, bet: Bet) -> None:
    """Reject pockets absent from this wheel."""
    if not isinstance(bet, Bet):
        raise TypeError("bet must be a Bet")
    if not set(bet.numbers).issubset(pockets(wheel)):
        raise ValueError("bet contains a pocket absent from the wheel")


def french_even_money(bet: Bet) -> bool:
    """Whether this coverage qualifies for a French zero concession."""
    return bet.payout == 1 and len(bet.numbers) == 18 and all(1 <= n <= 36 for n in bet.numbers)


def settle(wheel: Wheel, bet: Bet, outcome: int, *, imprisoned: bool = False) -> float | None:
    """Settle one spin; None retains an en-prison stake without new turnover.

    A released imprisoned win returns the original stake, hence net profit zero.
    Repeated zeros retain the imprisoned state until the first nonzero spin.
    """
    wheel = Wheel(wheel)
    validate_bet(wheel, bet)
    if type(outcome) is not int or outcome not in pockets(wheel):
        raise ValueError("outcome is absent from the wheel")
    if imprisoned:
        if wheel != Wheel.EN_PRISON or not french_even_money(bet):
            raise ValueError("imprisoned state requires an en-prison even-money wager")
        if outcome == 0:
            return None
        return 0.0 if outcome in bet.numbers else -1.0
    if french_even_money(bet) and outcome == 0:
        if wheel == Wheel.LA_PARTAGE:
            return -0.5
        if wheel == Wheel.EN_PRISON:
            return None
    return float(bet.payout) if outcome in bet.numbers else -1.0
