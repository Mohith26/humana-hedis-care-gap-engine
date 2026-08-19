"""Builders for FHIR R4 resources / bundles (plain dicts).

Used by both the seeded synthetic cohort generator and the hand-built gold cohort so
that every member — including gold-cohort members — flows through the *same* FHIR
loader the production path uses. All data produced here is SYNTHETIC (no real PHI).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from caregap import codes


def _iso(d: date) -> str:
    return d.isoformat()


def patient(member_id: str, gender: str, birth_date: date, deceased: bool = False) -> dict[str, Any]:
    res: dict[str, Any] = {
        "resourceType": "Patient",
        "id": member_id,
        "gender": gender,
        "birthDate": _iso(birth_date),
        # Explicit SYNTHETIC marker carried on every generated patient.
        "meta": {"tag": [{"system": "urn:caregap:data-classification", "code": "SYNTHETIC"}]},
    }
    if deceased:
        res["deceasedBoolean"] = True
    return res


def condition(member_id: str, code: str, onset: date | None, system: str = codes.SYSTEM_ICD10) -> dict[str, Any]:
    res: dict[str, Any] = {
        "resourceType": "Condition",
        "subject": {"reference": f"Patient/{member_id}"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"coding": [{"system": system, "code": code}]},
    }
    if onset is not None:
        res["onsetDateTime"] = _iso(onset)
    return res


def bp_observation(member_id: str, systolic: float, diastolic: float, when: date) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{member_id}"},
        "effectiveDateTime": _iso(when),
        "code": {"coding": [{"system": codes.SYSTEM_LOINC, "code": codes.LOINC_BP_PANEL}]},
        "component": [
            {
                "code": {"coding": [{"system": codes.SYSTEM_LOINC, "code": codes.LOINC_SYSTOLIC}]},
                "valueQuantity": {"value": systolic, "unit": "mmHg"},
            },
            {
                "code": {"coding": [{"system": codes.SYSTEM_LOINC, "code": codes.LOINC_DIASTOLIC}]},
                "valueQuantity": {"value": diastolic, "unit": "mmHg"},
            },
        ],
    }


def a1c_observation(member_id: str, value: float, when: date, code: str = "4548-4") -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{member_id}"},
        "effectiveDateTime": _iso(when),
        "code": {"coding": [{"system": codes.SYSTEM_LOINC, "code": code}]},
        "valueQuantity": {"value": value, "unit": "%"},
    }


def lab_observation(member_id: str, code: str, when: date, system: str = codes.SYSTEM_LOINC) -> dict[str, Any]:
    """A coded lab result without a numeric value (e.g. a FIT test event)."""
    return {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{member_id}"},
        "effectiveDateTime": _iso(when),
        "code": {"coding": [{"system": system, "code": code}]},
    }


def procedure(member_id: str, code: str, when: date, system: str = codes.SYSTEM_CPT) -> dict[str, Any]:
    return {
        "resourceType": "Procedure",
        "status": "completed",
        "subject": {"reference": f"Patient/{member_id}"},
        "performedDateTime": _iso(when),
        "code": {"coding": [{"system": system, "code": code}]},
    }


def bundle(resources: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap resources in a FHIR R4 collection Bundle."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "meta": {"tag": [{"system": "urn:caregap:data-classification", "code": "SYNTHETIC"}]},
        "entry": [{"resource": r} for r in resources],
    }
