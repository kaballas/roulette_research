"""Aggregate session risk without mistaking session win rate for an edge."""
from __future__ import annotations

import math
import numpy as np

from roulette.statistics import mean_interval, ratio_interval


def evaluate_sessions(data: dict[str, np.ndarray], house_edge: float,
                      comparisons: int = 1) -> dict:
    """Summarise independent sessions, including the staking-identity residual."""
    if not math.isfinite(house_edge) or house_edge < 0:
        raise ValueError("finite nonnegative house edge required")
    required = ("profit", "turnover", "max_drawdown", "ruined", "limit_stopped", "bankroll_stopped")
    if any(key not in data for key in required):
        raise ValueError("session data missing required metric")
    data = {key: np.asarray(value) for key, value in data.items()}
    shape = data["profit"].shape
    if len(shape) != 1 or shape[0] < 2 or any(data[key].shape != shape for key in required):
        raise ValueError("matching 1D vectors of at least two sessions required")
    if any(not np.all(np.isfinite(data[key])) for key in required):
        raise ValueError("finite session metrics required")
    if np.any(data["max_drawdown"] < 0):
        raise ValueError("drawdown must be nonnegative")
    if any(not np.all(np.isin(data[key], (0, 1))) for key in required[3:]):
        raise ValueError("terminal flags must be boolean")
    profit, turnover = data["profit"], data["turnover"]
    q = float(np.quantile(profit, .05))
    return {
        "sessions": len(profit),
        "mean_profit": mean_interval(profit, comparisons),
        "return_per_unit_staked": ratio_interval(profit, turnover, comparisons),
        "staking_identity_residual": mean_interval(profit + house_edge * turnover, comparisons),
        "mean_turnover": float(turnover.mean()),
        "winning_session_fraction": float(np.mean(profit > 0)),
        "ruin_fraction": float(np.mean(data["ruined"])),
        "limit_stop_fraction": float(np.mean(data["limit_stopped"])),
        "bankroll_stop_fraction": float(np.mean(data["bankroll_stopped"])),
        "mean_max_drawdown": float(data["max_drawdown"].mean()),
        "profit_fifth_percentile": q,
        "lower_tail_mean_including_ties": float(profit[profit <= q].mean()),
    }
