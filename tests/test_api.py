"""API endpoint behavior against the gold cohort (known values)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from caregap.api import create_app


@pytest.fixture(scope="module")
def client(gold_store):
    return TestClient(create_app(gold_store))


def _envelope_ok(payload):
    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["meta"]["synthetic"] is True
    assert payload["meta"]["data_classification"] == "SYNTHETIC"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    _envelope_ok(body)
    assert body["data"]["members"] == 26


def test_measures_rates(client):
    r = client.get("/measures")
    assert r.status_code == 200
    body = r.json()
    _envelope_ok(body)
    by_id = {m["measure_id"]: m for m in body["data"]}
    assert set(by_id) == {"CBP", "GSD", "EED", "BCS", "COL"}
    # CBP: eligible 5, compliant 2 (gold-01, gold-05).
    assert by_id["CBP"]["denominator"] == 5
    assert by_id["CBP"]["numerator"] == 2
    assert by_id["CBP"]["open_gaps"] == 3
    # GSD: eligible 6, compliant 2 (gold-07, gold-12); poor-control extra present.
    assert by_id["GSD"]["denominator"] == 6
    assert by_id["GSD"]["numerator"] == 2
    assert "poor_control" in by_id["GSD"]["extra"]


def test_member_care_gaps_uncontrolled(client):
    r = client.get("/members/gold-02-cbp-uncontrolled/care-gaps")
    assert r.status_code == 200
    body = r.json()
    _envelope_ok(body)
    data = body["data"]
    gap_measures = {g["measure_id"] for g in data["open_gaps"]}
    assert "CBP" in gap_measures
    cbp_reason = next(g["reason"] for g in data["open_gaps"] if g["measure_id"] == "CBP")
    assert "150/95" in cbp_reason
    assert data["open_gap_count"] == 2  # CBP + COL


def test_member_care_gaps_compliant_has_no_gaps(client):
    r = client.get("/members/gold-01-cbp-controlled/care-gaps")
    body = r.json()
    assert body["data"]["open_gap_count"] == 0
    cbp = next(m for m in body["data"]["measures"] if m["measure_id"] == "CBP")
    assert cbp["status"] == "compliant"


def test_member_not_found_404(client):
    r = client.get("/members/does-not-exist/care-gaps")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"]


def test_gaps_by_measure(client):
    r = client.get("/gaps?measure=CBP")
    assert r.status_code == 200
    body = r.json()
    _envelope_ok(body)
    assert body["data"]["open_gap_count"] == 3
    member_ids = {g["member_id"] for g in body["data"]["gaps"]}
    assert member_ids == {
        "gold-02-cbp-uncontrolled",
        "gold-03-cbp-out-of-window",
        "gold-04-cbp-missing",
    }


def test_gaps_unknown_measure_422(client):
    r = client.get("/gaps?measure=BOGUS")
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_gaps_missing_param_422(client):
    r = client.get("/gaps")
    assert r.status_code == 422


def test_outreach_ranked(client):
    r = client.get("/outreach")
    assert r.status_code == 200
    body = r.json()
    _envelope_ok(body)
    assert body["meta"]["total_members_with_gaps"] == 11
    top = body["data"][0]
    assert top["rank"] == 1
    assert top["member_id"] == "gold-08-gsd-uncontrolled"
    assert top["priority_score"] == 5.0
    # scores must be non-increasing
    scores = [e["priority_score"] for e in body["data"]]
    assert scores == sorted(scores, reverse=True)


def test_outreach_limit(client):
    r = client.get("/outreach?limit=2")
    body = r.json()
    assert len(body["data"]) == 2
    assert body["meta"]["returned"] == 2
