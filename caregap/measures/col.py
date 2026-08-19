"""COL — Colorectal Cancer Screening (HEDIS-style, simplified).

Denominator: members 45-75 (as of Dec 31 of the measurement year).
Numerator:   any appropriate screening within its modality-specific look-back window,
             all windows ending Dec 31 of the measurement year:
               * FIT / gFOBT (fecal occult blood)      — measurement year (1 yr)
               * FIT-DNA (Cologuard, sDNA-FIT)          — measurement year + 2 prior (3 yr)
               * Flexible sigmoidoscopy                 — measurement year + 4 prior (5 yr)
               * CT colonography                        — measurement year + 4 prior (5 yr)
               * Colonoscopy                            — measurement year + 9 prior (10 yr)
Gap:         eligible & no qualifying screening in any window.
"""

from __future__ import annotations

from datetime import date

from .. import codes
from ..model import Member
from .base import Measure, MeasureContext

_AGE_MIN = 45
_AGE_MAX = 75


class COL(Measure):
    measure_id = "COL"
    name = "Colorectal Cancer Screening"
    spec = (
        "Age 45-75 as of Dec 31; compliant if any appropriate screening in its window: "
        "FIT/gFOBT (1yr), FIT-DNA (3yr), flex sigmoidoscopy (5yr), CT colonography (5yr), "
        "colonoscopy (10yr)."
    )

    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        if member.deceased:
            return False
        age = member.age_as_of(ctx.year_end)
        return _AGE_MIN <= age <= _AGE_MAX

    def _screening_windows(self, ctx: MeasureContext) -> list[tuple[frozenset[str], date]]:
        end = ctx.year_end
        return [
            (codes.FIT_FOBT_CODES, date(ctx.year, 1, 1)),          # 1 year
            (codes.FIT_FOBT_LOINC, date(ctx.year, 1, 1)),          # 1 year (lab-coded FIT)
            (codes.FIT_DNA_CODES, date(ctx.year - 2, 1, 1)),       # 3 years
            (codes.FLEX_SIGMOIDOSCOPY_CODES, date(ctx.year - 4, 1, 1)),  # 5 years
            (codes.CT_COLONOGRAPHY_CODES, date(ctx.year - 4, 1, 1)),     # 5 years
            (codes.COLONOSCOPY_CODES, date(ctx.year - 9, 1, 1)),   # 10 years
        ]

    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        for code_set, start in self._screening_windows(ctx):
            if member.procedures_in(code_set, start, ctx.year_end):
                return True
            # FIT can also arrive as a lab Observation (LOINC-coded).
            if member.observations_in(code_set, start, ctx.year_end):
                return True
        return False

    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        return "no colorectal cancer screening in any qualifying look-back window"
