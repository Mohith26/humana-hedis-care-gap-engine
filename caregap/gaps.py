"""Care-gap detection: eligible & not compliant -> open gap (+ reason)."""

from __future__ import annotations

from dataclasses import dataclass

from .engine import evaluate_member
from .measures import STATUS_GAP, MeasureContext
from .model import Member


@dataclass(frozen=True)
class CareGap:
    """One open care gap for a member on one measure."""

    member_id: str
    measure_id: str
    reason: str


def member_gaps(member: Member, ctx: MeasureContext | None = None) -> list[CareGap]:
    """All open care gaps for one member."""
    return [
        CareGap(member_id=member.id, measure_id=s.measure_id, reason=s.reason or "")
        for s in evaluate_member(member, ctx)
        if s.status == STATUS_GAP
    ]


def all_gaps(members: list[Member], ctx: MeasureContext | None = None) -> list[CareGap]:
    """All open care gaps across a cohort (flattened)."""
    out: list[CareGap] = []
    for member in members:
        out.extend(member_gaps(member, ctx))
    return out


def gaps_for_measure(
    members: list[Member], measure_id: str, ctx: MeasureContext | None = None
) -> list[CareGap]:
    """All open gaps for a specific measure across the cohort."""
    return [g for g in all_gaps(members, ctx) if g.measure_id == measure_id]


def members_with_any_gap(members: list[Member], ctx: MeasureContext | None = None) -> int:
    """Count of members with at least one open care gap."""
    return sum(1 for m in members if member_gaps(m, ctx))
