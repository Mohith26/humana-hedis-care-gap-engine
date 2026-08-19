"""Measure registry — the ordered set of HEDIS-style measures the engine runs."""

from __future__ import annotations

from .base import (
    STATUS_COMPLIANT,
    STATUS_GAP,
    STATUS_NOT_ELIGIBLE,
    Measure,
    MeasureContext,
    PopulationResult,
)
from .bcs import BCS
from .cbp import CBP
from .col import COL
from .eed import EED
from .gsd import GSD

#: Canonical ordering used across the engine, API, and reports.
ALL_MEASURES: list[Measure] = [CBP(), GSD(), EED(), BCS(), COL()]

MEASURES_BY_ID: dict[str, Measure] = {m.measure_id: m for m in ALL_MEASURES}


def get_measure(measure_id: str) -> Measure:
    """Look up a measure by id, raising KeyError if unknown."""
    return MEASURES_BY_ID[measure_id]


__all__ = [
    "ALL_MEASURES",
    "MEASURES_BY_ID",
    "get_measure",
    "Measure",
    "MeasureContext",
    "PopulationResult",
    "STATUS_COMPLIANT",
    "STATUS_GAP",
    "STATUS_NOT_ELIGIBLE",
    "CBP",
    "GSD",
    "EED",
    "BCS",
    "COL",
]
