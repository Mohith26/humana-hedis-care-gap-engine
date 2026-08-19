"""FHIR loader: parse Patient/Condition/Observation/Procedure correctly."""

from __future__ import annotations

from datetime import date

import pytest

from caregap.fhir_loader import FHIRParseError, count_resources, load_member

from datagen import fhir_factory as ff


def test_parses_patient_demographics():
    b = ff.bundle([ff.patient("p1", "female", date(1970, 5, 6))])
    m = load_member(b)
    assert m.id == "p1"
    assert m.sex == "female"
    assert m.birth_date == date(1970, 5, 6)
    assert m.deceased is False


def test_parses_bp_components():
    b = ff.bundle([
        ff.patient("p1", "male", date(1965, 1, 1)),
        ff.bp_observation("p1", 148, 92, date(2025, 4, 1)),
    ])
    m = load_member(b)
    bp = m.observations[0]
    assert bp.code == "85354-9"
    assert bp.components["8480-6"] == 148.0
    assert bp.components["8462-4"] == 92.0
    assert bp.effective == date(2025, 4, 1)


def test_parses_a1c_value_and_condition():
    b = ff.bundle([
        ff.patient("p1", "male", date(1965, 1, 1)),
        ff.condition("p1", "E11.9", date(2019, 1, 1)),
        ff.a1c_observation("p1", 7.4, date(2025, 3, 1)),
    ])
    m = load_member(b)
    assert m.conditions[0].code == "E11.9"
    assert m.conditions[0].onset == date(2019, 1, 1)
    a1c = m.observations[0]
    assert a1c.value == 7.4
    assert a1c.unit == "%"


def test_parses_procedure():
    b = ff.bundle([
        ff.patient("p1", "male", date(1965, 1, 1)),
        ff.procedure("p1", "45378", date(2022, 6, 1)),
    ])
    m = load_member(b)
    assert m.procedures[0].code == "45378"
    assert m.procedures[0].performed == date(2022, 6, 1)


def test_deceased_flag():
    b = ff.bundle([ff.patient("p1", "male", date(1965, 1, 1), deceased=True)])
    assert load_member(b).deceased is True


def test_synthetic_tag_present_on_generated_bundle():
    b = ff.bundle([ff.patient("p1", "male", date(1965, 1, 1))])
    tags = b["meta"]["tag"]
    assert any(t["code"] == "SYNTHETIC" for t in tags)


def test_bundle_without_patient_raises():
    b = ff.bundle([ff.condition("p1", "I10", date(2019, 1, 1))])
    with pytest.raises(FHIRParseError):
        load_member(b)


def test_non_bundle_raises():
    with pytest.raises(FHIRParseError):
        load_member({"resourceType": "Patient"})


def test_partial_date_parses_to_first_of_period():
    b = ff.bundle([{"resourceType": "Patient", "id": "p1", "gender": "male", "birthDate": "1970"}])
    assert load_member(b).birth_date == date(1970, 1, 1)


def test_count_resources():
    b = ff.bundle([
        ff.patient("p1", "male", date(1965, 1, 1)),
        ff.condition("p1", "I10", date(2019, 1, 1)),
        ff.bp_observation("p1", 120, 70, date(2025, 4, 1)),
    ])
    assert count_resources([b]) == 3
