"""CBP — Controlling High Blood Pressure (HEDIS-style, simplified).

Denominator: members 18-85 (as of Dec 31 of the measurement year) with a
             hypertension diagnosis (ICD-10 I10) on or before the year end.
Numerator:   the most recent BP reading in the measurement year is < 140/90
             (systolic < 140 AND diastolic < 90).
Gap:         eligible & not compliant — no BP in the year, or last BP not controlled.
"""

from __future__ import annotations

from .. import codes, config
from ..model import Member
from .base import Measure, MeasureContext

_AGE_MIN = 18
_AGE_MAX = 85


class CBP(Measure):
    measure_id = "CBP"
    name = "Controlling High Blood Pressure"
    spec = (
        "Age 18-85 as of Dec 31 with hypertension (ICD-10 I10); compliant if the most "
        "recent BP in the measurement year is < 140/90."
    )

    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        if member.deceased:
            return False
        age = member.age_as_of(ctx.year_end)
        if not (_AGE_MIN <= age <= _AGE_MAX):
            return False
        return member.has_condition(codes.HYPERTENSION_ICD10, codes.SYSTEM_ICD10, ctx.year_end)

    def _latest_bp(self, member: Member, ctx: MeasureContext):
        panel = frozenset({codes.LOINC_BP_PANEL})
        readings = [
            o
            for o in member.observations_in(panel, ctx.year_start, ctx.year_end)
            if codes.LOINC_SYSTOLIC in o.components and codes.LOINC_DIASTOLIC in o.components
        ]
        if not readings:
            return None
        return max(readings, key=lambda o: o.effective)

    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        bp = self._latest_bp(member, ctx)
        if bp is None:
            return False
        systolic = bp.components[codes.LOINC_SYSTOLIC]
        diastolic = bp.components[codes.LOINC_DIASTOLIC]
        return (
            systolic < config.CBP_SYSTOLIC_THRESHOLD
            and diastolic < config.CBP_DIASTOLIC_THRESHOLD
        )

    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        bp = self._latest_bp(member, ctx)
        if bp is None:
            return "no blood-pressure reading recorded in the measurement year"
        systolic = int(bp.components[codes.LOINC_SYSTOLIC])
        diastolic = int(bp.components[codes.LOINC_DIASTOLIC])
        return f"last BP {systolic}/{diastolic} not controlled (needs < 140/90)"
