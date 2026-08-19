"""FastAPI service exposing the care-gap engine.

Endpoints (consistent envelope, every response tagged SYNTHETIC):
  GET /health                     — cohort size + measurement year + synthetic tag
  GET /measures                   — denominator/numerator/rate per measure
  GET /members/{id}/care-gaps     — a member's per-measure status + open gaps
  GET /gaps?measure=CBP           — population open gaps for one measure
  GET /outreach?limit=N           — risk-prioritized outreach worklist
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import config
from .engine import evaluate_member, population_results
from .gaps import gaps_for_measure, member_gaps, members_with_any_gap
from .measures import MEASURES_BY_ID
from .outreach import build_worklist
from .store import MemberStore

DEFAULT_DATA_DIR = os.environ.get(
    "CAREGAP_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic_fhir"),
)


class Envelope(BaseModel):
    """Consistent API response envelope."""

    success: bool
    data: Any | None = None
    error: str | None = None
    meta: dict[str, Any]


def _meta(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = {
        "synthetic": True,
        "data_classification": config.SYNTHETIC_TAG,
        "disclaimer": config.DATA_DISCLAIMER,
        "measurement_year": config.MEASUREMENT_YEAR,
    }
    if extra:
        meta.update(extra)
    return meta


def _ok(data: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "error": None, "meta": _meta(extra)}


def create_app(store: MemberStore | None = None) -> FastAPI:
    app = FastAPI(
        title="CareGap — HEDIS-style Care-Gap Engine (SYNTHETIC data, no PHI)",
        version="1.0.0",
        description=config.DATA_DISCLAIMER,
    )

    def get_store() -> MemberStore:
        if getattr(app.state, "store", None) is None:
            app.state.store = MemberStore.from_bundle_dir(DEFAULT_DATA_DIR)
        return app.state.store

    app.state.store = store

    @app.exception_handler(HTTPException)
    async def _http_exc(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.detail, "meta": _meta()},
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        s = get_store()
        return _ok({"status": "ok", "members": len(s)})

    @app.get("/measures")
    def measures() -> dict[str, Any]:
        s = get_store()
        results = population_results(s.members)
        data = [
            {
                "measure_id": r.measure_id,
                "name": r.name,
                "denominator": r.denominator,
                "numerator": r.numerator,
                "rate": round(r.rate, 4),
                "open_gaps": r.gaps,
                "extra": r.extra,
            }
            for r in results
        ]
        return _ok(data, {"n_members": len(s)})

    @app.get("/members/{member_id}/care-gaps")
    def member_care_gaps(member_id: str) -> dict[str, Any]:
        s = get_store()
        member = s.get(member_id)
        if member is None:
            raise HTTPException(status_code=404, detail=f"member {member_id!r} not found")
        statuses = evaluate_member(member)
        gaps = member_gaps(member)
        data = {
            "member_id": member.id,
            "sex": member.sex,
            "age": member.age_as_of(config.MEASUREMENT_YEAR_END),
            "measures": [
                {"measure_id": s.measure_id, "status": s.status, "reason": s.reason}
                for s in statuses
            ],
            "open_gaps": [
                {"measure_id": g.measure_id, "reason": g.reason} for g in gaps
            ],
            "open_gap_count": len(gaps),
        }
        return _ok(data)

    @app.get("/gaps")
    def gaps(measure: str = Query(..., description="measure id, e.g. CBP")) -> dict[str, Any]:
        s = get_store()
        measure = measure.upper()
        if measure not in MEASURES_BY_ID:
            raise HTTPException(
                status_code=422,
                detail=f"unknown measure {measure!r}; valid: {sorted(MEASURES_BY_ID)}",
            )
        found = gaps_for_measure(s.members, measure)
        data = {
            "measure_id": measure,
            "open_gap_count": len(found),
            "gaps": [
                {"member_id": g.member_id, "reason": g.reason} for g in found
            ],
        }
        return _ok(data)

    @app.get("/outreach")
    def outreach(
        limit: int = Query(50, ge=1, le=10000, description="max entries to return")
    ) -> dict[str, Any]:
        s = get_store()
        worklist = build_worklist(s.members)
        data = [
            {
                "rank": e.rank,
                "member_id": e.member_id,
                "gap_count": e.gap_count,
                "priority_score": e.priority_score,
                "gaps": [
                    {"measure_id": g.measure_id, "reason": g.reason} for g in e.gaps
                ],
            }
            for e in worklist[:limit]
        ]
        return _ok(
            data,
            {
                "total_members_with_gaps": members_with_any_gap(s.members),
                "returned": len(data),
            },
        )

    return app


# Module-level app for `uvicorn caregap.api:app` (lazy-loads the default data dir).
app = create_app()
