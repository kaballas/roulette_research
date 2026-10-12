"""Exact one-spin loss metrics and a frontier of supplied portfolio candidates.

Expected shortfall uses loss = -net profit and an upper tail of probability
``alpha`` (not a confidence level). The boundary atom is split to give exactly
that mass. These are one-spin measures, not session ruin or drawdown estimates.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

from roulette.coverage import CoverageAnalysis


@dataclass(frozen=True)
class ExactRisk:
    """Conditional means exclude zero profits; loss means are positive magnitudes."""

    total_stake: Fraction
    alpha: Fraction
    profitable_count: int
    worst_profit: Fraction
    conditional_positive_mean: Fraction | None
    conditional_loss_mean: Fraction | None
    expected_shortfall: Fraction


def _fraction(value: object) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("a finite rational number is required")
    try:
        return Fraction(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError("a finite rational number is required") from exc


def exact_risk(analysis: CoverageAnalysis, alpha: object = Fraction(1, 20)) -> ExactRisk:
    """Compute exact conditional means and average loss in the worst alpha mass.

    ``alpha=1/20`` means the worst 5% of outcomes. ``alpha=1`` gives expected
    loss across all pockets. Tail loss may include negative values (profits)
    when the selected tail exceeds the probability of a loss. A conditional
    mean is ``None`` when its conditioning event has zero probability.
    """
    tail_mass = _fraction(alpha)
    if not 0 < tail_mass <= 1:
        raise ValueError("alpha must be in (0, 1]")
    if not isinstance(analysis, CoverageAnalysis):
        raise ValueError("a CoverageAnalysis is required")
    profits = tuple(_fraction(value) for value in analysis.profits)
    if len(profits) != 37:
        raise ValueError("exactly 37 equally likely pocket profits are required")
    total_stake = _fraction(analysis.total_stake)
    if total_stake <= 0:
        raise ValueError("total stake must be positive")
    positives = tuple(value for value in profits if value > 0)
    losses = tuple(-value for value in profits if value < 0)
    remaining = tail_mass
    weighted_loss = Fraction(0)
    for profit in sorted(profits):
        mass = min(Fraction(1, 37), remaining)
        weighted_loss -= profit * mass
        remaining -= mass
        if remaining == 0:
            break
    return ExactRisk(
        total_stake, tail_mass, len(positives), min(profits),
        sum(positives, Fraction(0)) / len(positives) if positives else None,
        sum(losses, Fraction(0)) / len(losses) if losses else None,
        weighted_loss / tail_mass,
    )


def candidate_frontier(
    candidates: Mapping[str, CoverageAnalysis], alpha: object = Fraction(1, 20),
) -> tuple[str, ...]:
    """Return nondominated supplied candidate names, preserving input order.

    Prefer higher profitable count, higher worst profit and lower expected
    shortfall, with at least one strict improvement for dominance. Equal-metric
    candidates are retained. All candidates must have the same total stake so
    chip-denominated risks are comparable. This is a candidate frontier, never
    a claim of a globally optimal frontier over unsearched allocations.
    """
    metrics = {name: exact_risk(analysis, alpha) for name, analysis in candidates.items()}
    if len({risk.total_stake for risk in metrics.values()}) > 1:
        raise ValueError("candidate portfolios must have equal total stakes")

    def dominates(left: ExactRisk, right: ExactRisk) -> bool:
        weak = (left.profitable_count >= right.profitable_count
                and left.worst_profit >= right.worst_profit
                and left.expected_shortfall <= right.expected_shortfall)
        strict = (left.profitable_count > right.profitable_count
                  or left.worst_profit > right.worst_profit
                  or left.expected_shortfall < right.expected_shortfall)
        return weak and strict

    return tuple(name for name, risk in metrics.items()
                 if not any(dominates(other, risk) for other in metrics.values()))
