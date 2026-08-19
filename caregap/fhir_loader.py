"""FHIR R4 -> clinical model loader.

Parses FHIR R4 ``Bundle`` JSON (as produced by the seeded synthetic generator, and
shaped like Synthea output) into the immutable :mod:`caregap.model` types. Direct
JSON parsing (no external FHIR runtime dependency) with defensive validation at the
boundary — external data is never trusted.
"""

from __future__ import annotations

from datetime import date
from typing import Any


class FHIRParseError(ValueError):
    """Raised when a FHIR resource cannot be parsed into the clinical model."""


def _parse_date(value: Any) -> date | None:
    """Parse a FHIR date/dateTime string (YYYY, YYYY-MM, or full) into a date."""
    if not value or not isinstance(value, str):
        return None
    token = value.split("T", 1)[0]
    parts = token.split("-")
    try:
        if len(parts) == 1:
            return date(int(parts[0]), 1, 1)
        if len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1)
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError) as exc:  # malformed date component
        raise FHIRParseError(f"unparseable FHIR date: {value!r}") from exc


def _codings(concept: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not concept:
        return []
    coding = concept.get("coding")
    return coding if isinstance(coding, list) else []


def _resources(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise FHIRParseError("expected a FHIR Bundle resource")
    out: list[dict[str, Any]] = []
    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if isinstance(resource, dict) and resource.get("resourceType"):
            out.append(resource)
    return out


# --- per-resource parsers -------------------------------------------------

from .model import Condition, Member, Observation, Procedure  # noqa: E402


def _parse_condition(res: dict[str, Any]) -> list[Condition]:
    onset = _parse_date(res.get("onsetDateTime"))
    out = []
    for coding in _codings(res.get("code")):
        code = coding.get("code")
        system = coding.get("system", "")
        if code:
            out.append(Condition(code=str(code), system=str(system), onset=onset))
    return out


def _parse_observation(res: dict[str, Any]) -> list[Observation]:
    effective = _parse_date(res.get("effectiveDateTime"))
    codings = _codings(res.get("code"))
    if not codings:
        return []
    # Build component map (systolic/diastolic panels) keyed by component LOINC code.
    components: dict[str, float] = {}
    for comp in res.get("component", []) or []:
        for c in _codings(comp.get("code")):
            qty = comp.get("valueQuantity") or {}
            if c.get("code") is not None and isinstance(qty.get("value"), (int, float)):
                components[str(c["code"])] = float(qty["value"])
    qty = res.get("valueQuantity") or {}
    value = float(qty["value"]) if isinstance(qty.get("value"), (int, float)) else None
    unit = qty.get("unit")
    out = []
    for coding in codings:
        code = coding.get("code")
        system = coding.get("system", "")
        if code:
            out.append(
                Observation(
                    code=str(code),
                    system=str(system),
                    effective=effective,
                    value=value,
                    unit=str(unit) if unit else None,
                    components=dict(components),
                )
            )
    return out


def _parse_procedure(res: dict[str, Any]) -> list[Procedure]:
    performed = _parse_date(res.get("performedDateTime")) or _parse_date(
        (res.get("performedPeriod") or {}).get("start")
    )
    out = []
    for coding in _codings(res.get("code")):
        code = coding.get("code")
        system = coding.get("system", "")
        if code:
            out.append(Procedure(code=str(code), system=str(system), performed=performed))
    return out


def _normalize_sex(value: Any) -> str:
    if value in ("male", "female"):
        return value
    return "unknown"


def load_member(bundle: dict[str, Any]) -> Member:
    """Parse one FHIR Bundle (one member) into a :class:`Member`.

    The bundle must contain exactly one Patient resource.
    """
    resources = _resources(bundle)
    patient = next((r for r in resources if r.get("resourceType") == "Patient"), None)
    if patient is None:
        raise FHIRParseError("bundle has no Patient resource")

    birth = _parse_date(patient.get("birthDate"))
    if birth is None:
        raise FHIRParseError(f"Patient {patient.get('id')} has no birthDate")

    deceased = bool(patient.get("deceasedBoolean")) or bool(patient.get("deceasedDateTime"))

    conditions: list[Condition] = []
    observations: list[Observation] = []
    procedures: list[Procedure] = []
    for res in resources:
        rtype = res.get("resourceType")
        if rtype == "Condition":
            conditions.extend(_parse_condition(res))
        elif rtype == "Observation":
            observations.extend(_parse_observation(res))
        elif rtype == "Procedure":
            procedures.extend(_parse_procedure(res))

    return Member(
        id=str(patient.get("id") or ""),
        sex=_normalize_sex(patient.get("gender")),
        birth_date=birth,
        deceased=deceased,
        conditions=tuple(conditions),
        observations=tuple(observations),
        procedures=tuple(procedures),
    )


def load_cohort(bundles: list[dict[str, Any]]) -> list[Member]:
    """Parse many bundles into members, preserving order."""
    return [load_member(b) for b in bundles]


def count_resources(bundles: list[dict[str, Any]]) -> int:
    """Total number of FHIR resources across all bundles (for scale reporting)."""
    return sum(len(_resources(b)) for b in bundles)
