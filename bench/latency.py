"""API latency: p50/p95 for /measures and /members/{id}/care-gaps.

Measured in-process via FastAPI's TestClient (ASGI) — this excludes the HTTP/TCP
network socket and reflects the gateway's real per-request work. Stated honestly.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

from caregap import config
from caregap.api import create_app

from .common import DEFAULT_COHORT_SIZE, DEFAULT_SEED, build_store, percentile


def _time_endpoint(client: TestClient, path: str, iterations: int, warmup: int) -> dict[str, Any]:
    latencies: list[float] = []
    for i in range(iterations + warmup):
        start = time.perf_counter()
        resp = client.get(path)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert resp.status_code == 200, f"{path} -> {resp.status_code}"
        if i >= warmup:
            latencies.append(elapsed_ms)
    latencies.sort()
    return {
        "requests": len(latencies),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
        "mean_ms": round(sum(latencies) / len(latencies), 3),
    }


def measure_latency(
    n: int = DEFAULT_COHORT_SIZE,
    seed: int = DEFAULT_SEED,
    iterations: int = 200,
    warmup: int = 20,
) -> dict[str, Any]:
    store = build_store(n, seed)
    app = create_app(store)
    client = TestClient(app)
    sample_id = store.ids()[0]

    return {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "data_classification": config.SYNTHETIC_TAG,
        "methodology": "in-process FastAPI TestClient (ASGI); excludes network socket",
        "cohort_size": len(store),
        "iterations": iterations,
        "warmup_excluded": warmup,
        "measures_endpoint": _time_endpoint(client, "/measures", iterations, warmup),
        "care_gaps_endpoint": _time_endpoint(
            client, f"/members/{sample_id}/care-gaps", iterations, warmup
        ),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(measure_latency(), indent=2))
