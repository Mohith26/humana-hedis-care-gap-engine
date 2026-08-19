"""Shared benchmark helpers."""

from __future__ import annotations

from caregap.fhir_loader import load_cohort
from caregap.model import Member
from caregap.store import MemberStore

from datagen.generator import generate_cohort

DEFAULT_COHORT_SIZE = 1000
DEFAULT_SEED = 42


def build_cohort(n: int = DEFAULT_COHORT_SIZE, seed: int = DEFAULT_SEED) -> list[Member]:
    """Generate + load a synthetic cohort of ``n`` members."""
    return load_cohort(generate_cohort(n, seed))


def build_store(n: int = DEFAULT_COHORT_SIZE, seed: int = DEFAULT_SEED) -> MemberStore:
    return MemberStore(build_cohort(n, seed))


def percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile of an already-sorted list (pct in [0, 100])."""
    if not sorted_values:
        raise ValueError("no values")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac
