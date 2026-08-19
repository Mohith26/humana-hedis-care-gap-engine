"""Engine: run all measures over a cohort -> per-member statuses + population rates."""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .measures import ALL_MEASURES, STATUS_GAP, MeasureContext, PopulationResult
from .measures.gsd import GSD
from .model import Member


@dataclass(frozen=True)
class MemberMeasureStatus:
    """One member's result for one measure."""

    measure_id: str
    status: str  # not_eligible | compliant | gap
    reason: str | None  # gap reason when status == gap


def default_context() -> MeasureContext:
    return MeasureContext.from_year(config.MEASUREMENT_YEAR)


def evaluate_member(member: Member, ctx: MeasureContext | None = None) -> list[MemberMeasureStatus]:
    """Evaluate every measure for one member."""
    ctx = ctx or default_context()
    out: list[MemberMeasureStatus] = []
    for measure in ALL_MEASURES:
        status = measure.status(member, ctx)
        reason = measure.gap_reason(member, ctx) if status == STATUS_GAP else None
        out.append(MemberMeasureStatus(measure.measure_id, status, reason))
    return out


def population_results(
    members: list[Member], ctx: MeasureContext | None = None
) -> list[PopulationResult]:
    """Compute denominator / numerator / rate (+ extras) per measure over a cohort."""
    ctx = ctx or default_context()
    results: list[PopulationResult] = []
    for measure in ALL_MEASURES:
        denominator = 0
        numerator = 0
        gaps = 0
        poor_control = 0
        for member in members:
            if not measure.in_denominator(member, ctx):
                continue
            denominator += 1
            if measure.is_compliant(member, ctx):
                numerator += 1
            else:
                gaps += 1
            if isinstance(measure, GSD) and measure.is_poor_control(member, ctx):
                poor_control += 1
        extra: dict[str, float] = {}
        if isinstance(measure, GSD):
            extra["poor_control"] = poor_control
        results.append(
            PopulationResult(
                measure_id=measure.measure_id,
                name=measure.name,
                denominator=denominator,
                numerator=numerator,
                gaps=gaps,
                extra=extra,
            )
        )
    return results
