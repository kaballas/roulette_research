"""Independent precision, clustered covariance and risk-summary checks."""
from fractions import Fraction
from itertools import product
from math import ceil, sqrt

import numpy as np
import pytest
from scipy.stats import norm

from roulette.evaluation import evaluate_sessions
from roulette.statistics import critical_value, mean_interval, ratio_interval, required_sample_size


def test_predeclared_samples_and_precision():
    z = norm.isf(.01/16)
    assert critical_value(8) == pytest.approx(z)
    assert required_sample_size(46656/1369,.03,8) == 394384
    assert required_sample_size(5401/5476,.03,8) == 11414
    n = required_sample_size(46656/1369,.03,8)
    assert z*sqrt((46656/1369)/n) <= .03
    assert z*sqrt((46656/1369)/(n-1)) > .03
    assert required_sample_size(0,.03,8) == 2
    assert critical_value(48) > critical_value(8) > critical_value(1)


def test_mean_interval_uses_independent_session_standard_error():
    result = mean_interval(np.array([0.,1.,2.]),comparisons=8)
    assert result['estimate'] == 1
    assert result['se'] == pytest.approx(1/sqrt(3))
    assert result['high']-1 == pytest.approx(norm.isf(.01/16)/sqrt(3))
    assert 1-result['low'] == pytest.approx(result['high']-1)


def test_cluster_ratio_covariance_and_aggregate_denominator():
    p = np.array([0.,1.,4.])
    s = np.array([1.,2.,3.])
    result = ratio_interval(p,s,comparisons=8)
    # Exact residuals p-r*s are -5/6,-2/3,3/2, sample variance61/36.
    assert result['estimate'] == pytest.approx(5/6)
    assert result['estimate'] != pytest.approx(np.mean(p/s))
    assert result['se'] == pytest.approx(sqrt(61)/(12*sqrt(3)))
    scaled = ratio_interval(p*7,s*7,comparisons=8)
    assert scaled == pytest.approx(result)
    # Perfect profit/turnover correlation must cancel rather than inflate SE.
    perfect = ratio_interval(.25*s,s)
    assert perfect['estimate'] == .25
    assert perfect['se'] == 0


@pytest.mark.parametrize('comparisons,alpha',[(0,.01),(-1,.01),(1.5,.01),(True,.01),(1,0),(1,1),(1,float('nan'))])
def test_invalid_multiplicity(comparisons,alpha):
    with pytest.raises((ValueError,TypeError)):
        critical_value(comparisons,alpha)


@pytest.mark.parametrize('variance,width',[(-1,.1),(float('nan'),.1),(float('inf'),.1),(1,0),(1,-1),(1,float('inf'))])
def test_invalid_precision(variance,width):
    with pytest.raises((ValueError,TypeError)):
        required_sample_size(variance,width)


@pytest.mark.parametrize('values',[[],[1],[[1,2]],[1,float('nan')],[1,float('inf')]])
def test_invalid_mean_observations(values):
    with pytest.raises(ValueError):
        mean_interval(np.array(values))


@pytest.mark.parametrize('profit,stake',[([1],[1]),([1,2],[1]),([1,2],[0,0]),([1,2],[1,-1]),
    ([1,2],[1,float('inf')]),([1,float('nan')],[1,2]),([[1,2]],[[1,2]])])
def test_invalid_ratio_observations(profit,stake):
    with pytest.raises(ValueError):
        ratio_interval(np.array(profit),np.array(stake))


def sample_data():
    return dict(profit=np.array([-10.,-2.,0.,4.]),turnover=np.array([10.,6.,2.,4.]),
                ruined=np.array([True,False,False,False]),
                limit_stopped=np.array([False,False,False,True]),
                bankroll_stopped=np.array([False,True,False,False]),
                max_drawdown=np.array([10.,4.,1.,2.]))


def test_summary_keeps_distinct_terminal_flags_and_tail():
    result = evaluate_sessions(sample_data(),.1,comparisons=3)
    assert result['sessions'] == 4
    assert result['winning_session_fraction'] == .25
    assert result['ruin_fraction'] == .25
    assert result['limit_stop_fraction'] == .25
    assert result['bankroll_stop_fraction'] == .25
    assert result['mean_profit']['estimate'] == -2
    assert result['return_per_unit_staked']['estimate'] == pytest.approx(-8/22)
    assert result['staking_identity_residual']['estimate'] == pytest.approx(-1.45)
    assert result['mean_max_drawdown'] == 4.25
    assert result['lower_tail_mean_including_ties'] == -10


@pytest.mark.parametrize('key',['ruined','limit_stopped','bankroll_stopped','max_drawdown'])
def test_summary_rejects_misaligned_observations(key):
    data = sample_data()
    data[key] = data[key][:-1]
    with pytest.raises(ValueError):
        evaluate_sessions(data,.1)


@pytest.mark.parametrize('edge',[-.1,float('nan'),float('inf')])
def test_summary_rejects_invalid_house_edge(edge):
    with pytest.raises(ValueError):
        evaluate_sessions(sample_data(),edge)


def test_three_step_finite_martingale_identity_by_exact_enumeration():
    p = Fraction(18,37)
    expected_profit = Fraction(0)
    expected_stake = Fraction(0)
    for wins in product([False,True],repeat=3):
        probability = Fraction(1)
        for win in wins:
            probability *= p if win else 1-p
        funds,stake,profit,turnover = 5,1,0,0
        for win in wins:
            if stake > funds or stake > 4:
                break
            turnover += stake
            change = stake if win else -stake
            profit += change
            funds += change
            stake = 1 if win else stake*2
        expected_profit += probability*profit
        expected_stake += probability*turnover
    assert expected_profit == -expected_stake/37
    assert expected_profit < 0


@pytest.mark.parametrize('key,value',[('ruined',2),('limit_stopped',-.1),
    ('bankroll_stopped',float('nan')),('max_drawdown',-1),('max_drawdown',float('inf'))])
def test_summary_rejects_invalid_terminal_metrics(key,value):
    data = sample_data()
    data[key] = data[key].astype(float)
    data[key][0] = value
    with pytest.raises(ValueError):
        evaluate_sessions(data,.1)


def test_summary_rejects_missing_metric():
    data = sample_data()
    del data['ruined']
    with pytest.raises(ValueError):
        evaluate_sessions(data,.1)
