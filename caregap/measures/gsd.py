"""GSD — Glycemic Status Assessment for Patients With Diabetes (HbA1c control).

(HEDIS-style, simplified; formerly HBD — Hemoglobin A1c Control for Diabetes.)

Denominator: members 18-75 (as of Dec 31 of the measurement year) with diabetes
             (ICD-10 E10.x / E11.x) on or before the year end.
Numerator:   the most recent HbA1c in the measurement year is < 8.0%.
Poor control (reported separately): most recent HbA1c > 9.0% (or no A1c on record).
Gap:         eligible & not compliant — no A1c in the year, or last A1c >= 8.0%.
"""

from __future__ import annotations

from .. import codes, config
from ..model import Member
from .base import Measure, MeasureContext

_AGE_MIN = 18
_AGE_MAX = 75


class GSD(Measure):
    measure_id = "GSD"
    name = "Glycemic Status (HbA1c) Control for Diabetes"
    spec = (
        "Age 18-75 as of Dec 31 with diabetes (ICD-10 E10.x/E11.x); compliant if the "
        "most recent HbA1c in the measurement year is < 8.0% (poor control if > 9.0%)."
    )

    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        if member.deceased:
            return False
        age = member.age_as_of(ctx.year_end)
        if not (_AGE_MIN <= age <= _AGE_MAX):
            return False
        return member.has_condition(codes.DIABETES_ICD10, codes.SYSTEM_ICD10, ctx.year_end)

    def _latest_a1c(self, member: Member, ctx: MeasureContext):
        return member.most_recent_observation(
            codes.HBA1C_LOINC, ctx.year_start, ctx.year_end
        )

    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        a1c = self._latest_a1c(member, ctx)
        if a1c is None or a1c.value is None:
            return False
        return a1c.value < config.GSD_A1C_CONTROL_THRESHOLD

    def is_poor_control(self, member: Member, ctx: MeasureContext) -> bool:
        """HEDIS 'poor control' proxy: most recent A1c > 9.0%, or no A1c on record."""
        a1c = self._latest_a1c(member, ctx)
        if a1c is None or a1c.value is None:
            return True
        return a1c.value > config.GSD_A1C_POOR_CONTROL_THRESHOLD

    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        a1c = self._latest_a1c(member, ctx)
        if a1c is None or a1c.value is None:
            return "no HbA1c result recorded in the measurement year"
        return f"last HbA1c {a1c.value:.1f}% not controlled (needs < 8.0%)"
