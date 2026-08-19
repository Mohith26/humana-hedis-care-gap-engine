"""BCS — Breast Cancer Screening (HEDIS-style, simplified).

Denominator: women 50-74 (as of Dec 31 of the measurement year), excluding members
             with evidence of bilateral mastectomy.
Numerator:   a mammogram any time in the 27-month look-back window — from Oct 1 two
             years before the measurement year through Dec 31 of the measurement year.
Gap:         eligible & no mammogram in the look-back window.
"""

from __future__ import annotations

from datetime import date

from .. import codes
from ..model import Member
from .base import Measure, MeasureContext

_AGE_MIN = 50
_AGE_MAX = 74


class BCS(Measure):
    measure_id = "BCS"
    name = "Breast Cancer Screening"
    spec = (
        "Women 50-74 as of Dec 31 (excluding bilateral mastectomy); compliant if a "
        "mammogram occurred in the 27-month window (Oct 1 two years prior -> Dec 31)."
    )

    @staticmethod
    def lookback_start(ctx: MeasureContext) -> date:
        return date(ctx.year - 2, 10, 1)

    def _excluded(self, member: Member, ctx: MeasureContext) -> bool:
        # Bilateral mastectomy anytime on or before the measurement year end.
        early = date(1900, 1, 1)
        if member.procedures_in(codes.BILATERAL_MASTECTOMY_CPT, early, ctx.year_end):
            return True
        return member.has_condition(
            codes.BILATERAL_MASTECTOMY_ICD10, codes.SYSTEM_ICD10, ctx.year_end
        )

    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        if member.deceased or member.sex != "female":
            return False
        age = member.age_as_of(ctx.year_end)
        if not (_AGE_MIN <= age <= _AGE_MAX):
            return False
        return not self._excluded(member, ctx)

    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        return bool(
            member.procedures_in(
                codes.MAMMOGRAM_CODES, self.lookback_start(ctx), ctx.year_end
            )
        )

    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        return "no mammogram in the 27-month screening look-back window"
