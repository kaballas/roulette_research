"""Predeclared sample sizes and approximate simultaneous confidence intervals."""
from __future__ import annotations

import math
import numpy as np
from scipy.stats import norm


def critical_value(comparisons: int = 1, alpha: float = .01) -> float:
    """Bonferroni two-sided normal critical value; coverage is asymptotic."""
    if type(comparisons) is not int or comparisons < 1 or not 0 < alpha < 1:
        raise ValueError("positive comparisons and alpha in (0,1) required")
    return float(norm.ppf(1 - alpha / (2 * comparisons)))


def required_sample_size(variance: float, halfwidth: float,
                         comparisons: int = 1, alpha: float = .01) -> int:
    """Choose fixed n from exact variance before observing outcomes."""
    if not math.isfinite(variance) or variance < 0 or not math.isfinite(halfwidth) or halfwidth <= 0:
        raise ValueError("finite nonnegative variance and positive halfwidth required")
    return max(2, math.ceil(critical_value(comparisons, alpha) ** 2 * variance / halfwidth ** 2))


def mean_interval(values: np.ndarray, comparisons: int = 1,
                  alpha: float = .01) -> dict[str, float]:
    """Independent-observation mean interval, with estimated standard error."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.all(np.isfinite(x)):
        raise ValueError("at least two finite independent observations required")
    mean = float(x.mean())
    se = float(x.std(ddof=1) / math.sqrt(len(x)))
    halfwidth = critical_value(comparisons, alpha) * se
    return {"estimate": mean, "se": se, "low": mean - halfwidth, "high": mean + halfwidth}


def ratio_interval(profits: np.ndarray, stakes: np.ndarray,
                   comparisons: int = 1, alpha: float = .01) -> dict[str, float]:
    """Ratio of aggregate profit to stake; independent sessions are clusters.

    Uses the delta method, retaining within-session profit/turnover covariance.
    Spins within a progression must not be treated as independent samples.
    """
    p, s = np.asarray(profits, dtype=float), np.asarray(stakes, dtype=float)
    if p.ndim != 1 or p.shape != s.shape or len(p) < 2:
        raise ValueError("matching vectors of at least two sessions required")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(s)) or np.any(s < 0) or s.mean() <= 0:
        raise ValueError("finite observations and positive total stake required")
    ratio = float(p.sum() / s.sum())
    se = float((p - ratio * s).std(ddof=1) / (math.sqrt(len(p)) * s.mean()))
    width = critical_value(comparisons, alpha) * se
    return {"estimate": ratio, "se": se, "low": ratio - width, "high": ratio + width}
