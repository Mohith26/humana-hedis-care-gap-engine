"""Targeted unit tests for each measure's boundary logic (direct model construction)."""

from __future__ import annotations

from datetime import date

from caregap.measures import MeasureContext
from caregap.measures.bcs import BCS
from caregap.measures.cbp import CBP
from caregap.measures.col import COL
from caregap.measures.eed import EED
from caregap.measures.gsd import GSD
from caregap.model import Condition, Member, Observation, Procedure

CTX = MeasureContext.from_year(2025)
ICD10 = "http://hl7.org/fhir/sid/icd-10-cm"


def _member(sex="male", birth=date(1970, 1, 1), conditions=(), observations=(), procedures=(), deceased=False):
    return Member(
        id="t",
        sex=sex,
        birth_date=birth,
        deceased=deceased,
        conditions=tuple(conditions),
        observations=tuple(observations),
        procedures=tuple(procedures),
    )


def _htn():
    return Condition("I10", ICD10, date(2018, 1, 1))


def _dm():
    return Condition("E11.9", ICD10, date(2018, 1, 1))


def _bp(sys_v, dia_v, when):
    return Observation(
        code="85354-9", system="http://loinc.org", effective=when,
        components={"8480-6": float(sys_v), "8462-4": float(dia_v)},
    )


def _a1c(value, when):
    return Observation(code="4548-4", system="http://loinc.org", effective=when, value=value, unit="%")


# --- CBP ------------------------------------------------------------------
def test_cbp_controlled_is_compliant():
    m = _member(birth=date(1965, 1, 1), conditions=[_htn()], observations=[_bp(128, 78, date(2025, 6, 1))])
    assert CBP().status(m, CTX) == "compliant"


def test_cbp_high_systolic_is_gap():
    m = _member(birth=date(1965, 1, 1), conditions=[_htn()], observations=[_bp(150, 85, date(2025, 6, 1))])
    assert CBP().status(m, CTX) == "gap"


def test_cbp_uses_most_recent_reading():
    m = _member(birth=date(1965, 1, 1), conditions=[_htn()],
                observations=[_bp(120, 70, date(2025, 1, 1)), _bp(160, 100, date(2025, 9, 1))])
    assert CBP().status(m, CTX) == "gap"  # latest (160/100) governs


def test_cbp_out_of_window_reading_is_gap():
    m = _member(birth=date(1965, 1, 1), conditions=[_htn()], observations=[_bp(120, 70, date(2024, 12, 31))])
    assert CBP().status(m, CTX) == "gap"
    assert "no blood-pressure" in CBP().gap_reason(m, CTX)


def test_cbp_age_85_eligible_86_not():
    controlled = [_bp(120, 70, date(2025, 6, 1))]
    m85 = _member(birth=date(1940, 1, 1), conditions=[_htn()], observations=controlled)  # age 85
    m86 = _member(birth=date(1939, 1, 1), conditions=[_htn()], observations=controlled)  # age 86
    assert CBP().in_denominator(m85, CTX) is True
    assert CBP().in_denominator(m86, CTX) is False


def test_cbp_requires_hypertension():
    m = _member(birth=date(1965, 1, 1), observations=[_bp(120, 70, date(2025, 6, 1))])
    assert CBP().status(m, CTX) == "not_eligible"


# --- GSD ------------------------------------------------------------------
def test_gsd_controlled_and_poor_control_flag():
    ok = _member(birth=date(1975, 1, 1), conditions=[_dm()], observations=[_a1c(6.8, date(2025, 5, 1))])
    poor = _member(birth=date(1975, 1, 1), conditions=[_dm()], observations=[_a1c(10.2, date(2025, 5, 1))])
    assert GSD().status(ok, CTX) == "compliant"
    assert GSD().is_poor_control(ok, CTX) is False
    assert GSD().status(poor, CTX) == "gap"
    assert GSD().is_poor_control(poor, CTX) is True


def test_gsd_boundary_8_percent_is_gap():
    m = _member(birth=date(1975, 1, 1), conditions=[_dm()], observations=[_a1c(8.0, date(2025, 5, 1))])
    assert GSD().status(m, CTX) == "gap"  # compliant requires < 8.0 (strict)


def test_gsd_missing_a1c_is_gap_and_poor():
    m = _member(birth=date(1975, 1, 1), conditions=[_dm()])
    assert GSD().status(m, CTX) == "gap"
    assert GSD().is_poor_control(m, CTX) is True
    assert "no HbA1c" in GSD().gap_reason(m, CTX)


def test_gsd_age_75_eligible_76_not():
    obs = [_a1c(7.0, date(2025, 5, 1))]
    m75 = _member(birth=date(1950, 1, 1), conditions=[_dm()], observations=obs)
    m76 = _member(birth=date(1949, 1, 1), conditions=[_dm()], observations=obs)
    assert GSD().in_denominator(m75, CTX) is True
    assert GSD().in_denominator(m76, CTX) is False


# --- EED ------------------------------------------------------------------
def test_eed_exam_in_year_compliant_out_of_year_gap():
    cpt = "http://www.ama-assn.org/go/cpt"
    ok = _member(birth=date(1975, 1, 1), conditions=[_dm()], procedures=[Procedure("92014", cpt, date(2025, 3, 1))])
    stale = _member(birth=date(1975, 1, 1), conditions=[_dm()], procedures=[Procedure("92014", cpt, date(2024, 3, 1))])
    assert EED().status(ok, CTX) == "compliant"
    assert EED().status(stale, CTX) == "gap"


# --- BCS ------------------------------------------------------------------
def test_bcs_male_ineligible():
    m = _member(sex="male", birth=date(1965, 1, 1))
    assert BCS().status(m, CTX) == "not_eligible"


def test_bcs_lookback_window_boundary():
    cpt = "http://www.ama-assn.org/go/cpt"
    inside = _member(sex="female", birth=date(1965, 1, 1), procedures=[Procedure("77067", cpt, date(2023, 10, 1))])
    outside = _member(sex="female", birth=date(1965, 1, 1), procedures=[Procedure("77067", cpt, date(2023, 9, 30))])
    assert BCS().status(inside, CTX) == "compliant"
    assert BCS().status(outside, CTX) == "gap"


def test_bcs_age_74_eligible_75_not():
    m74 = _member(sex="female", birth=date(1951, 1, 1))
    m75 = _member(sex="female", birth=date(1950, 1, 1))
    assert BCS().in_denominator(m74, CTX) is True
    assert BCS().in_denominator(m75, CTX) is False


def test_bcs_mastectomy_excludes():
    cpt = "http://www.ama-assn.org/go/cpt"
    m = _member(sex="female", birth=date(1965, 1, 1), procedures=[Procedure("19303", cpt, date(2020, 1, 1))])
    assert BCS().in_denominator(m, CTX) is False


# --- COL ------------------------------------------------------------------
def test_col_colonoscopy_10yr_window():
    cpt = "http://www.ama-assn.org/go/cpt"
    inside = _member(birth=date(1965, 1, 1), procedures=[Procedure("45378", cpt, date(2016, 6, 1))])
    outside = _member(birth=date(1965, 1, 1), procedures=[Procedure("45378", cpt, date(2015, 6, 1))])
    assert COL().status(inside, CTX) == "compliant"
    assert COL().status(outside, CTX) == "gap"


def test_col_fit_one_year_only():
    cpt = "http://www.ama-assn.org/go/cpt"
    inside = _member(birth=date(1965, 1, 1), procedures=[Procedure("82270", cpt, date(2025, 2, 1))])
    outside = _member(birth=date(1965, 1, 1), procedures=[Procedure("82270", cpt, date(2024, 12, 31))])
    assert COL().status(inside, CTX) == "compliant"
    assert COL().status(outside, CTX) == "gap"


def test_col_lab_coded_fit_observation_counts():
    loinc = "http://loinc.org"
    m = _member(birth=date(1965, 1, 1), observations=[Observation("2335-8", loinc, date(2025, 2, 1))])
    assert COL().status(m, CTX) == "compliant"


def test_col_age_45_eligible_44_not():
    m45 = _member(birth=date(1980, 1, 1))
    m44 = _member(birth=date(1981, 1, 1))
    assert COL().in_denominator(m45, CTX) is True
    assert COL().in_denominator(m44, CTX) is False


def test_deceased_excluded_from_all():
    m = _member(birth=date(1965, 1, 1), conditions=[_htn(), _dm()],
                observations=[_bp(120, 70, date(2025, 6, 1)), _a1c(6.5, date(2025, 6, 1))], deceased=True)
    for measure in (CBP(), GSD(), EED(), COL()):
        assert measure.in_denominator(m, CTX) is False
