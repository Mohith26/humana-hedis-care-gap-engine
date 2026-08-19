"""Every gold-cohort member's per-measure status must match its known truth.

This is the core correctness test: for all 26 hand-authored members x 5 measures, the
engine's classification (not_eligible / compliant / gap) is asserted against the
ground-truth label, covering age boundaries, out-of-window results, missing data,
poor control, sex ineligibility, and the mastectomy exclusion.
"""

from __future__ import annotations

import pytest

from caregap.engine import default_context
from caregap.fhir_loader import load_member
from caregap.measures import ALL_MEASURES

from datagen.gold_cohort import build_gold_cohort

_GOLD = build_gold_cohort()
_CASES = [
    (gm.member_id, gm.scenario, gm, measure.measure_id)
    for gm in _GOLD
    for measure in ALL_MEASURES
]


@pytest.mark.parametrize(
    "member_id,scenario,gm,measure_id",
    _CASES,
    ids=[f"{c[0]}::{c[3]}" for c in _CASES],
)
def test_gold_member_measure_status(member_id, scenario, gm, measure_id):
    ctx = default_context()
    member = load_member(gm.bundle)
    measure = next(m for m in ALL_MEASURES if m.measure_id == measure_id)

    actual = measure.status(member, ctx)
    expected = gm.expected[measure_id]

    assert actual == expected, (
        f"{member_id} [{measure_id}]: expected {expected!r}, got {actual!r} "
        f"({scenario})"
    )


def test_gold_cohort_covers_all_measures_both_ways():
    """Each measure must have >=1 true gap AND >=1 true compliant in the gold cohort,
    so precision/recall are well-defined (non-degenerate)."""
    for measure in ALL_MEASURES:
        labels = [gm.expected[measure.measure_id] for gm in _GOLD]
        assert "gap" in labels, f"{measure.measure_id}: no true gap in gold cohort"
        assert "compliant" in labels, f"{measure.measure_id}: no true compliant in gold cohort"
        assert "not_eligible" in labels, f"{measure.measure_id}: no ineligible member in gold cohort"
