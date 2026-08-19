"""Risk-prioritized outreach worklist.

Members are ranked by a priority score = sum over their open gaps of the measure's
Stars weight (CMS triple-weights intermediate-outcome measures; process measures 1x).
This surfaces members whose open gaps carry the most Stars impact first.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .gaps import CareGap, member_gaps
from .measures import MeasureContext
from .model import Member


def gap_weight(measure_id: str) -> float:
    return config.MEASURE_WEIGHTS.get(measure_id, config.DEFAULT_MEASURE_WEIGHT)


@dataclass(frozen=True)
class OutreachEntry:
    """One member's slot on the prioritized outreach worklist."""

    rank: int
    member_id: str
    gap_count: int
    priority_score: float
    gaps: tuple[CareGap, ...]


def build_worklist(
    members: list[Member], ctx: MeasureContext | None = None
) -> list[OutreachEntry]:
    """Return members with >=1 open gap, ranked by weighted priority (desc).

    Priority score = sum of Stars weights over the member's open gaps. Ties are
    broken by raw gap count, then member id, so the ordering is deterministic.
    """
    scored: list[tuple[float, int, str, list[CareGap]]] = []
    for member in members:
        gaps = member_gaps(member, ctx)
        if not gaps:
            continue
        score = sum(gap_weight(g.measure_id) for g in gaps)
        scored.append((score, len(gaps), member.id, gaps))

    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))

    return [
        OutreachEntry(
            rank=i + 1,
            member_id=member_id,
            gap_count=len(gaps),
            priority_score=round(score, 4),
            gaps=tuple(gaps),
        )
        for i, (score, _cnt, member_id, gaps) in enumerate(scored)
    ]
