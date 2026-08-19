"""Measure abstraction shared by all HEDIS-style measures.

Each measure decides, for one member and a :class:`MeasureContext`:
  * ``in_denominator`` — eligible (age/sex/diagnosis) and not excluded
  * ``is_compliant``   — numerator met (only meaningful if in denominator)
  * ``gap_reason``     — human-readable reason when there is an open gap

``status`` folds these into one of three labels used everywhere downstream and in
the correctness eval: ``not_eligible`` | ``compliant`` | ``gap``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..model import Member

STATUS_NOT_ELIGIBLE = "not_eligible"
STATUS_COMPLIANT = "compliant"
STATUS_GAP = "gap"


@dataclass(frozen=True)
class MeasureContext:
    """Evaluation context — the measurement year and its window boundaries."""

    year: int
    year_start: date
    year_end: date

    @classmethod
    def from_year(cls, year: int) -> "MeasureContext":
        return cls(year=year, year_start=date(year, 1, 1), year_end=date(year, 12, 31))


class Measure(ABC):
    """Base class for a single HEDIS-style quality measure."""

    #: short measure id, e.g. "CBP"
    measure_id: str
    #: human name
    name: str
    #: one-line spec description (code sets + age/sex/window/threshold)
    spec: str

    @abstractmethod
    def in_denominator(self, member: Member, ctx: MeasureContext) -> bool:
        """Eligible population membership (age/sex/diagnosis + exclusions)."""

    @abstractmethod
    def is_compliant(self, member: Member, ctx: MeasureContext) -> bool:
        """Numerator: whether the member met the measure (assumes eligibility)."""

    @abstractmethod
    def gap_reason(self, member: Member, ctx: MeasureContext) -> str:
        """Reason string for an open gap (assumes eligible & not compliant)."""

    def status(self, member: Member, ctx: MeasureContext) -> str:
        if not self.in_denominator(member, ctx):
            return STATUS_NOT_ELIGIBLE
        return STATUS_COMPLIANT if self.is_compliant(member, ctx) else STATUS_GAP


@dataclass(frozen=True)
class PopulationResult:
    """Aggregate measure result over a cohort."""

    measure_id: str
    name: str
    denominator: int
    numerator: int
    gaps: int
    extra: dict[str, float]  # measure-specific extras (e.g. poor-control count)

    @property
    def rate(self) -> float:
        """Compliance rate = numerator / denominator (0.0 when denominator is 0)."""
        return (self.numerator / self.denominator) if self.denominator else 0.0
