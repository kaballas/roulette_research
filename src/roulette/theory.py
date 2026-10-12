"""Exact completed-wager profit distributions and moments using SymPy."""

from sympy import Rational

from .rules import Bet, Wheel, french_even_money, pockets, settle, validate_bet


def distribution(wheel: Wheel, bet: Bet) -> dict[Rational, Rational]:
    """Probability law of net profit per initial unit, including prison release."""
    wheel = Wheel(wheel)
    validate_bet(wheel, bet)
    if wheel == Wheel.EN_PRISON and french_even_money(bet):
        # Initial win/loss 18/37 each; zero then eventual win/loss 1/74 each.
        return {Rational(1): Rational(18, 37), Rational(0): Rational(1, 74), Rational(-1): Rational(1, 2)}
    result: dict[Rational, Rational] = {}
    probability = Rational(1, len(pockets(wheel)))
    for outcome in pockets(wheel):
        value = settle(wheel, bet, outcome)
        assert value is not None
        profit = Rational(str(value))
        result[profit] = result.get(profit, Rational(0)) + probability
    return result


def moments(wheel: Wheel, bet: Bet) -> tuple[Rational, Rational]:
    """Return exact expected profit and variance per unit of initial stake."""
    law = distribution(wheel, bet)
    mean = sum((profit * probability for profit, probability in law.items()), Rational(0))
    variance = sum(((profit - mean) ** 2 * probability for profit, probability in law.items()), Rational(0))
    return mean, variance
