"""Seeded synthetic generator: determinism, SYNTHETIC tagging, loadability."""

from __future__ import annotations

import json

from caregap.engine import population_results
from caregap.fhir_loader import load_cohort

from datagen.generator import generate_cohort


def test_generator_is_deterministic():
    a = generate_cohort(50, seed=42)
    b = generate_cohort(50, seed=42)
    assert json.dumps(a) == json.dumps(b)


def test_different_seed_differs():
    a = generate_cohort(50, seed=42)
    b = generate_cohort(50, seed=7)
    assert json.dumps(a) != json.dumps(b)


def test_every_bundle_tagged_synthetic():
    for bundle in generate_cohort(30, seed=42):
        assert any(t["code"] == "SYNTHETIC" for t in bundle["meta"]["tag"])
        patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        assert any(t["code"] == "SYNTHETIC" for t in patient["meta"]["tag"])


def test_cohort_loads_and_has_nonempty_denominators():
    members = load_cohort(generate_cohort(300, seed=42))
    assert len(members) == 300
    results = {r.measure_id: r for r in population_results(members)}
    # With 300 seeded members every measure should have a non-empty denominator.
    for mid in ("CBP", "GSD", "EED", "BCS", "COL"):
        assert results[mid].denominator > 0, f"{mid} empty denominator"
        assert 0.0 <= results[mid].rate <= 1.0


def test_member_ids_unique():
    members = load_cohort(generate_cohort(200, seed=42))
    ids = [m.id for m in members]
    assert len(set(ids)) == len(ids)
