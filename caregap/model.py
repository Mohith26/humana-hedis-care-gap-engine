"""Immutable clinical domain model.

The FHIR loader parses raw FHIR R4 bundles into these frozen dataclasses; measures
read them. Kept storage-agnostic and free of FHIR-specific structure so measure
logic stays simple.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Condition:
    """A diagnosis (typically ICD-10-CM)."""

    code: str
    system: str
    onset: date | None = None


@dataclass(frozen=True)
class Observation:
    """A lab/vital observation.

    ``value``/``unit`` hold a simple quantity (e.g. an HbA1c %). ``components``
    holds multi-component observations such as a blood-pressure panel keyed by
    LOINC component code (e.g. ``{"8480-6": 148.0, "8462-4": 92.0}``).
    """

    code: str
    system: str
    effective: date | None = None
    value: float | None = None
    unit: str | None = None
    components: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Procedure:
    """A performed procedure/screening (CPT / HCPCS / CPT-II / SNOMED)."""

    code: str
    system: str
    performed: date | None = None


@dataclass(frozen=True)
class Member:
    """A member's parsed clinical record. SYNTHETIC — never real PHI."""

    id: str
    sex: str  # "male" | "female" | "unknown"
    birth_date: date
    deceased: bool = False
    conditions: tuple[Condition, ...] = ()
    observations: tuple[Observation, ...] = ()
    procedures: tuple[Procedure, ...] = ()

    def age_as_of(self, ref: date) -> int:
        """Completed years of age as of ``ref`` (HEDIS uses Dec 31 of the year)."""
        had_birthday = (ref.month, ref.day) >= (self.birth_date.month, self.birth_date.day)
        return ref.year - self.birth_date.year - (0 if had_birthday else 1)

    def has_condition(self, codes: frozenset[str], system: str, on_or_before: date) -> bool:
        """True if the member has an active diagnosis in ``codes`` (matching
        ``system``) with onset on or before ``on_or_before`` (or unknown onset)."""
        for cond in self.conditions:
            if cond.system == system and cond.code in codes:
                if cond.onset is None or cond.onset <= on_or_before:
                    return True
        return False

    def procedures_in(
        self, codes: frozenset[str], start: date, end: date
    ) -> list[Procedure]:
        """All procedures whose code is in ``codes`` and performed within [start, end]."""
        return [
            p
            for p in self.procedures
            if p.code in codes and p.performed is not None and start <= p.performed <= end
        ]

    def observations_in(
        self, codes: frozenset[str], start: date, end: date
    ) -> list[Observation]:
        """All observations whose code is in ``codes`` and dated within [start, end]."""
        return [
            o
            for o in self.observations
            if o.code in codes and o.effective is not None and start <= o.effective <= end
        ]

    def most_recent_observation(
        self, codes: frozenset[str], start: date, end: date
    ) -> Observation | None:
        """The latest observation in ``codes`` within [start, end], or None."""
        hits = self.observations_in(codes, start, end)
        if not hits:
            return None
        return max(hits, key=lambda o: o.effective)  # type: ignore[arg-type]
