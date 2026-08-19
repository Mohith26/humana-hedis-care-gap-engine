"""Gap detection + risk-prioritized outreach ordering."""

from __future__ import annotations

from datetime import date

from caregap.gaps import member_gaps, members_with_any_gap
from caregap.model import Condition, Member, Observation
from caregap.outreach import build_worklist, gap_weight

ICD10 = "http://hl7.org/fhir/sid/icd-10-cm"
LOINC = "http://loinc.org"


def _bp(sys_v, dia_v, when=date(2025, 6, 1)):
    return Observation(code="85354-9", system=LOINC, effective=when,
                       components={"8480-6": float(sys_v), "8462-4": float(dia_v)})


def _a1c(value, when=date(2025, 6, 1)):
    return Observation(code="4548-4", system=LOINC, effective=when, value=value, unit="%")


def _member(mid, birth, conditions=(), observations=()):
    return Member(id=mid, sex="male", birth_date=birth, conditions=tuple(conditions),
                  observations=tuple(observations))


def test_open_gap_has_reason():
    m = _member("m1", date(1965, 1, 1), [Condition("I10", ICD10, date(2018, 1, 1))],
                [_bp(150, 95)])
    gaps = member_gaps(m)
    cbp = [g for g in gaps if g.measure_id == "CBP"]
    assert len(cbp) == 1
    assert "150/95" in cbp[0].reason


def test_compliant_member_has_no_gap():
    m = _member("m1", date(1965, 1, 1), [Condition("I10", ICD10, date(2018, 1, 1))],
                [_bp(120, 70)])
    assert not [g for g in member_gaps(m) if g.measure_id == "CBP"]


def test_weights_triple_for_outcome_measures():
    assert gap_weight("CBP") == 3.0
    assert gap_weight("GSD") == 3.0
    assert gap_weight("EED") == 1.0
    assert gap_weight("BCS") == 1.0
    assert gap_weight("COL") == 1.0


def test_outreach_ranked_by_weighted_score():
    # A: one CBP gap (weight 3) + one COL gap (weight 1) = score 4, 2 gaps.
    a = _member("A", date(1965, 1, 1), [Condition("I10", ICD10, date(2018, 1, 1))])  # no BP -> CBP gap; age 60 -> COL gap
    # B: diabetes gaps (GSD weight 3 + EED weight 1) + COL gap 1 = score 5, 3 gaps.
    b = _member("B", date(1970, 1, 1), [Condition("E11.9", ICD10, date(2018, 1, 1))])  # no A1c/eye -> GSD+EED gaps; COL gap
    # C: single COL gap (weight 1), 1 gap.
    c = _member("C", date(1968, 1, 1))  # age 57 -> COL eligible, no screen -> gap

    worklist = build_worklist([a, b, c])
    order = [e.member_id for e in worklist]
    assert order == ["B", "A", "C"]  # by weighted score desc: 5, 4, 1
    assert worklist[0].priority_score == 5.0
    assert worklist[0].gap_count == 3
    assert worklist[0].rank == 1
    assert worklist[1].priority_score == 4.0  # A: CBP(3) + COL(1)


def test_members_with_any_gap_count():
    healthy = _member("H", date(1995, 1, 1))  # 30yo, no conditions -> no gaps
    gappy = _member("G", date(1965, 1, 1), [Condition("I10", ICD10, date(2018, 1, 1))])  # gaps
    assert members_with_any_gap([healthy, gappy]) == 1


def test_worklist_excludes_members_without_gaps():
    healthy = _member("H", date(1995, 1, 1))
    assert build_worklist([healthy]) == []
