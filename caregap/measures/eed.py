"""EED — Eye Exam for Patients With Diabetes (HEDIS-style, simplified).

Denominator: members 18-75 (as of Dec 31 of the measurement year) with diabetes
             (same eligible population as GSD).
Numerator:   a diabetic retinal / dilated eye exam performed in the measurement year.
             (Simplified: the real measure also credits a prior-year negative
             retinopathy screen; this engine requires an exam in the measurement year.)
Gap:         eligible & no qualifying eye exam in the measurement year.
"""

from __future__ import annotations

from .. import codes
from ..model import Member
from .base import Measure, MeasureContext

_AGE_MIN = 18
_AGE_MAX = 75


class EED(Measure):
    measure_id = "EED"
    name = "Eye Exam for Patients With Diabetes"
    spec = (
        "Age 18-75 as of Dec 31 with diabetes; compliant if a diabetic retinal/dilated "
        "eye exam (CPT/CPT-II eye-exam codes) was performed in the measurement year."
    )

    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        if member.deceased:
            return False
        age = member.age_as_of(ctx.year_end)
        if not (_AGE_MIN <= age <= _AGE_MAX):
            return False
        return member.has_condition(codes.DIABETES_ICD10, codes.SYSTEM_ICD10, ctx.year_end)

    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        return bool(
            member.procedures_in(codes.EYE_EXAM_CODES, ctx.year_start, ctx.year_end)
        )

    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        return "no diabetic eye exam recorded in the measurement year"
