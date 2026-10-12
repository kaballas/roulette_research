"""Deterministic simulator checks against an independent scalar wheel model."""
import numpy as np
import pytest

from roulette.rules import RED, STRAIGHT_ZERO, Wheel
from roulette.simulation import simulate_wagers


def reference(wheel, bet, n, seed):
    rng = np.random.default_rng(seed)
    size = 38 if wheel == Wheel.AMERICAN else 37
    result = []
    for _ in range(n):
        outcome = int(rng.integers(size))
        if wheel == Wheel.LA_PARTAGE and len(bet.numbers) == 18 and outcome == 0:
            profit = -0.5
        elif wheel == Wheel.EN_PRISON and len(bet.numbers) == 18 and outcome == 0:
            while outcome == 0:
                outcome = int(rng.integers(size))
            profit = 0 if outcome in bet.numbers else -1
        else:
            profit = bet.payout if outcome in bet.numbers else -1
        result.append(profit)
    return np.asarray(result,dtype=float)


@pytest.mark.parametrize("wheel", list(Wheel))
@pytest.mark.parametrize("bet", [RED,STRAIGHT_ZERO])
def test_simulated_wagers_support_mean_and_replay(wheel,bet):
    # Stream batching may differ from scalar reference for prison resolution;
    # exact seed replay is tested separately from distribution checks.
    result = simulate_wagers(wheel,bet,20000,12345)
    assert result.shape == (20000,)
    assert np.array_equal(result,simulate_wagers(wheel,bet,20000,12345))
    expected_support = {-1,bet.payout}
    if bet == RED and wheel == Wheel.LA_PARTAGE:
        expected_support.add(-0.5)
    if bet == RED and wheel == Wheel.EN_PRISON:
        expected_support.add(0)
    assert set(np.unique(result)) == expected_support
    oracle = reference(wheel,bet,20000,12345)
    # This is a smoke test, deliberately wider than registered experiment CIs.
    # It complements exact payout enumeration and does not replace it.
    tolerance = 0.20 if bet == STRAIGHT_ZERO else 0.08
    assert abs(float(result.mean()-oracle.mean())) < tolerance
    if wheel != Wheel.EN_PRISON or bet != RED:
        assert np.array_equal(result,oracle)


@pytest.mark.parametrize("n", [0,-1,1.5,True])
def test_invalid_wager_count(n):
    with pytest.raises((ValueError,TypeError)):
        simulate_wagers(Wheel.EUROPEAN,RED,n,0)


def test_one_wager_and_distinct_seed():
    assert simulate_wagers(Wheel.EUROPEAN,RED,1,0).shape == (1,)
    assert not np.array_equal(simulate_wagers(Wheel.EUROPEAN,RED,1000,0),simulate_wagers(Wheel.EUROPEAN,RED,1000,1))


def test_repeated_prison_zeros_with_known_release(monkeypatch):
    class ScriptedRNG:
        def __init__(self):
            self.calls = iter([np.array([0,0,1,2]),np.array([0,2]),np.array([1])])
        def choice(self, values, size):
            result = next(self.calls)
            assert len(result) == size
            return result
    monkeypatch.setattr("roulette.simulation.np.random.default_rng", lambda seed: ScriptedRNG())
    assert np.array_equal(simulate_wagers(Wheel.EN_PRISON,RED,4,0),[0,-1,1,-1])


@pytest.mark.parametrize("strategy,loss_stake,win_stake", [
    ("flat",1,1),("martingale",2,1),("reverse_martingale",1,2),
    ("fibonacci",1,1),("dalembert",2,1),("labouchere",5,2),
])
def test_strategy_first_update(strategy,loss_stake,win_stake):
    from roulette.strategies import make_strategy
    state = make_strategy(strategy,3,1)
    initial = 4 if strategy == "labouchere" else 1
    assert np.array_equal(state.stakes(),[initial,initial,initial])
    state.update(np.array([0,1,2]),np.array([-1.,1.,0.]))
    assert np.array_equal(state.stakes(),[loss_stake,win_stake,initial])


def test_martingale_resets_and_reverse_caps_three_wins():
    from roulette.strategies import make_strategy
    state = make_strategy("martingale",1,1)
    for expected in (2,4,8):
        state.update(np.array([0]),np.array([-1.]))
        assert state.stakes()[0] == expected
    state.update(np.array([0]),np.array([1.]))
    assert state.stakes()[0] == 1
    state = make_strategy("reverse_martingale",1,1)
    for expected in (2,4,1):
        state.update(np.array([0]),np.array([1.]))
        assert state.stakes()[0] == expected


@pytest.mark.parametrize("strategy", ["flat","martingale","reverse_martingale","fibonacci","dalembert","labouchere"])
def test_session_accounting_and_limits(strategy):
    from roulette.simulation import simulate_sessions
    params = dict(wheel=Wheel.EUROPEAN,bet=RED,strategy=strategy,sessions=100,
                  max_wagers=40,bankroll=25,table_min=1,table_max=8,seed=88)
    result = simulate_sessions(**params)
    replay = simulate_sessions(**params)
    for key in result:
        assert np.array_equal(result[key],replay[key])
    assert np.all(result["profit"] >= -25)
    assert np.all(result["wagers"] <= 40)
    assert np.array_equal(result["spins"],result["wagers"])
    assert np.all(result["turnover"] >= result["wagers"])
    assert np.all(result["turnover"] <= 8*result["wagers"])
    assert np.all(result["max_drawdown"] >= 0)
    assert np.all(result["max_drawdown"] >= np.maximum(0,-result["profit"]))
    assert np.array_equal(result["ruined"],25+result["profit"] == 0)


def test_no_bet_when_base_cannot_be_funded():
    from roulette.simulation import simulate_sessions
    result = simulate_sessions(Wheel.EUROPEAN,RED,"flat",5,20,0.5,1,10,0)
    assert np.all(result["wagers"] == 0)
    assert np.all(result["turnover"] == 0)
    assert np.all(result["profit"] == 0)
    assert np.all(result["bankroll_stopped"])
    assert not np.any(result["ruined"])


def test_reject_stake_above_table_max():
    from roulette.simulation import simulate_sessions
    result = simulate_sessions(Wheel.EUROPEAN,RED,"flat",5,20,100,1,2,0,base=3)
    assert np.all(result["wagers"] == 0)
    assert np.all(result["limit_stopped"])
    assert np.all(result["turnover"] == 0)


def scripted_rng(monkeypatch, outcomes):
    class ScriptedRNG:
        def __init__(self):
            self.values = iter(outcomes)
        def choice(self, values, size):
            drawn = np.array(next(self.values))
            assert len(drawn) == size
            assert set(drawn).issubset(values)
            return drawn
    monkeypatch.setattr("roulette.simulation.np.random.default_rng",lambda seed: ScriptedRNG())


def test_martingale_finite_bankroll_no_clipping(monkeypatch):
    from roulette.simulation import simulate_sessions
    scripted_rng(monkeypatch,[[2],[2]])
    result = simulate_sessions(Wheel.EUROPEAN,RED,"martingale",1,10,5,1,100,0)
    assert result["profit"][0] == -3
    assert result["turnover"][0] == 3
    assert result["wagers"][0] == 2
    assert result["bankroll_stopped"][0]
    assert not result["ruined"][0]


def test_session_prison_completed_wager_accounting(monkeypatch):
    from roulette.simulation import simulate_sessions
    scripted_rng(monkeypatch,[[0],[0],[1],[2]])
    result = simulate_sessions(Wheel.EN_PRISON,RED,"martingale",1,2,10,1,100,0)
    # Released win has zero profit, so it does not advance the progression.
    assert result["profit"][0] == -1
    assert result["turnover"][0] == 2
    assert result["wagers"][0] == 2
    assert result["spins"][0] == 4
    assert result["max_drawdown"][0] == 1


def test_ruin_flag_on_last_wager(monkeypatch):
    from roulette.simulation import simulate_sessions
    scripted_rng(monkeypatch,[[2]])
    result = simulate_sessions(Wheel.EUROPEAN,RED,"flat",1,1,1,1,100,0)
    assert result["profit"][0] == -1
    assert result["ruined"][0]


@pytest.mark.parametrize("changes", [dict(sessions=0),dict(sessions=True),dict(max_wagers=0),
    dict(bankroll=0),dict(bankroll=float("nan")),dict(table_min=0),dict(table_max=float("inf")),
    dict(table_min=3,table_max=2),dict(base=-1)])
def test_invalid_session_configuration(changes):
    from roulette.simulation import simulate_sessions
    params=dict(wheel=Wheel.EUROPEAN,bet=RED,strategy="flat",sessions=2,max_wagers=2,
                bankroll=10,table_min=1,table_max=100,seed=0)
    params.update(changes)
    with pytest.raises((ValueError,TypeError)):
        simulate_sessions(**params)


def test_mixed_portfolio_uses_same_spin(monkeypatch):
    from roulette.simulation import simulate_sessions
    from roulette.strategies import MIXED
    scripted_rng(monkeypatch,[[0,1,2]])
    result = simulate_sessions(Wheel.EUROPEAN,MIXED,"flat",3,1,100,1,64,0,base=2)
    # Two units total: red/zero components each get one unit.
    assert np.array_equal(result["profit"],[34,0,-2])
    assert np.array_equal(result["turnover"],[2,2,2])
    assert np.array_equal(result["spins"],[1,1,1])


def test_portfolio_component_minimum_enforced():
    from roulette.simulation import simulate_sessions
    from roulette.strategies import MIXED
    result = simulate_sessions(Wheel.EUROPEAN,MIXED,"flat",2,5,100,1,64,0,base=1)
    assert np.all(result["wagers"] == 0)
    assert np.all(result["limit_stopped"])


@pytest.mark.parametrize("wheel", [Wheel.LA_PARTAGE,Wheel.EN_PRISON])
def test_french_portfolios_rejected(wheel):
    from roulette.simulation import simulate_sessions
    from roulette.strategies import MIXED
    with pytest.raises(ValueError):
        simulate_sessions(wheel,MIXED,"flat",2,5,100,1,64,0,base=2)


def test_fully_staked_sector_loss_is_exact_ruin(monkeypatch):
    from roulette.simulation import simulate_sessions
    from roulette.strategies import SECTOR
    scripted_rng(monkeypatch,[[0]])
    result = simulate_sessions(Wheel.EUROPEAN,SECTOR,"flat",1,5,6,1,6,0,base=6)
    assert result["profit"][0] == -6
    assert result["ruined"][0]
    assert result["wagers"][0] == 1


def test_fibonacci_continues_beyond_initial_lookup():
    from roulette.strategies import make_strategy
    state = make_strategy("fibonacci",1,1)
    values = [1.,1.]
    for _ in range(85):
        values.append(values[-1]+values[-2])
    for _ in range(82):
        state.update(np.array([0]),np.array([-1.]))
    assert state.stakes()[0] == values[82]


def test_half_loss_advances_stake_and_french_accounting(monkeypatch):
    from roulette.simulation import simulate_sessions
    scripted_rng(monkeypatch,[[0],[1]])
    result = simulate_sessions(Wheel.LA_PARTAGE,RED,"martingale",1,2,10,1,64,0)
    assert result["profit"][0] == 1.5
    assert result["turnover"][0] == 3
    assert result["spins"][0] == 2
    assert result["max_drawdown"][0] == .5


def test_fibonacci_loss_progression_and_win_back_two():
    from roulette.strategies import make_strategy
    state = make_strategy("fibonacci",1,1)
    for expected in (1,2,3,5,8):
        state.update(np.array([0]),np.array([-1.]))
        assert state.stakes()[0] == expected
    state.update(np.array([0]),np.array([1.]))
    assert state.stakes()[0] == 3


def test_labouchere_cancels_and_restarts():
    from roulette.strategies import make_strategy
    state = make_strategy("labouchere",1,1)
    state.update(np.array([0]),np.array([1.]))
    assert state.stakes()[0] == 2
    state.update(np.array([0]),np.array([1.]))
    assert state.stakes()[0] == 4
