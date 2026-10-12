"""Independent exact enumeration and explicit settlement examples."""
from fractions import Fraction

import pytest
from sympy import Rational

from roulette.rules import Bet, RED, STRAIGHT_ZERO, Wheel, pockets, settle, straight
from roulette.theory import distribution, moments


@pytest.mark.parametrize("wheel,size", [(Wheel.EUROPEAN,37),(Wheel.AMERICAN,38),(Wheel.LA_PARTAGE,37),(Wheel.EN_PRISON,37)])
def test_wheel_pockets(wheel, size):
    assert pockets(wheel) == tuple(range(size))


@pytest.mark.parametrize("wheel", list(Wheel))
@pytest.mark.parametrize("count,payout", [(1,35),(2,17),(3,11),(4,8),(6,5),(12,2),(18,1)])
def test_standard_payout_exact_enumeration(wheel, count, payout):
    # Exclude zero from even-money bets so French rules apply unambiguously.
    bet = Bet(f"coverage_{count}", tuple(range(1,count+1)), payout)
    n = len(pockets(wheel))
    if count == 18 and wheel == Wheel.EN_PRISON:
        expected = {Rational(-1):Rational(1,2), Rational(0):Rational(1,74), Rational(1):Rational(18,37)}
    else:
        values = [Fraction(payout) if x in bet.numbers else Fraction(-1) for x in range(n)]
        if count == 18 and wheel == Wheel.LA_PARTAGE:
            values[0] = Fraction(-1,2)
        expected = {Rational(v.numerator,v.denominator):Rational(values.count(v),n) for v in set(values)}
    actual = distribution(wheel, bet)
    assert actual == expected
    mean = sum(v*p for v,p in expected.items())
    variance = sum((v-mean)**2*p for v,p in expected.items())
    assert moments(wheel,bet) == (mean,variance)
    assert sum(actual.values()) == 1


@pytest.mark.parametrize("wheel", list(Wheel))
def test_straight_zero_and_double_zero(wheel):
    assert settle(wheel, STRAIGHT_ZERO, 0) == 35
    assert settle(wheel, STRAIGHT_ZERO, 1) == -1
    if wheel == Wheel.AMERICAN:
        assert settle(wheel, straight(37), 37) == 35
        assert settle(wheel, STRAIGHT_ZERO, 37) == -1
    else:
        with pytest.raises(ValueError):
            settle(wheel, straight(37), 0)


def test_red_pockets_are_independent_known_set():
    assert set(RED.numbers) == {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    assert RED.payout == 1


def test_french_zero_mechanics():
    assert settle(Wheel.LA_PARTAGE, RED, 0) == -0.5
    assert settle(Wheel.EN_PRISON, RED, 0) is None
    assert settle(Wheel.EN_PRISON, RED, 0, imprisoned=True) is None
    assert settle(Wheel.EN_PRISON, RED, 1, imprisoned=True) == 0
    assert settle(Wheel.EN_PRISON, RED, 2, imprisoned=True) == -1
    assert settle(Wheel.EN_PRISON, RED, 1) == 1
    assert settle(Wheel.EN_PRISON, RED, 2) == -1
    for wheel in (Wheel.LA_PARTAGE, Wheel.EN_PRISON):
        assert settle(wheel, straight(1), 0) == -1
        assert moments(wheel, straight(1))[0] == Rational(-1,37)


def test_american_basket_exception():
    bet = Bet("basket", (0,1,2,3,37), 6)
    assert moments(Wheel.AMERICAN,bet)[0] == Rational(-3,38)
    assert settle(Wheel.AMERICAN,bet,37) == 6
    assert settle(Wheel.AMERICAN,bet,4) == -1
    with pytest.raises(ValueError):
        distribution(Wheel.EUROPEAN,bet)


@pytest.mark.parametrize("numbers,payout", [((),35),((1,1),17),((-1,),35),((38,),35),((1,),-1),((1,),1.5)])
def test_invalid_bet_rejected(numbers,payout):
    with pytest.raises((ValueError,TypeError)):
        bet = Bet("invalid",numbers,payout)
        distribution(Wheel.EUROPEAN,bet)


@pytest.mark.parametrize("outcome", [-1,37,38,1.5])
def test_invalid_european_outcome(outcome):
    with pytest.raises((ValueError,TypeError)):
        settle(Wheel.EUROPEAN,RED,outcome)


def test_invalid_prison_state_rejected():
    for wheel in (Wheel.EUROPEAN,Wheel.AMERICAN,Wheel.LA_PARTAGE):
        with pytest.raises(ValueError):
            settle(wheel,RED,1,imprisoned=True)
    with pytest.raises(ValueError):
        settle(Wheel.EN_PRISON,STRAIGHT_ZERO,0,imprisoned=True)


def test_french_concession_requires_zero_excluded():
    # Synthetic standard-count portfolio containing zero is not an outside bet.
    bet = Bet("zero_included_18",tuple(range(18)),1)
    for wheel in (Wheel.LA_PARTAGE,Wheel.EN_PRISON):
        assert settle(wheel,bet,0) == 1
        assert moments(wheel,bet)[0] == Rational(-1,37)


@pytest.mark.parametrize("numbers", [([1],),((True,),),((1.0,),)])
def test_non_integer_or_mutable_pocket_rejected(numbers):
    with pytest.raises((ValueError,TypeError)):
        Bet("invalid",numbers[0],35)
