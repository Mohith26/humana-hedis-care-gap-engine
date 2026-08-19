"""Throughput: members processed per second through the full measure engine."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from caregap import config
from caregap.engine import evaluate_member
from caregap.model import Member

from .common import DEFAULT_COHORT_SIZE, DEFAULT_SEED, build_cohort


def measure_throughput(
    n: int = DEFAULT_COHORT_SIZE, seed: int = DEFAULT_SEED, repeats: int = 5
) -> dict[str, Any]:
    """Evaluate every measure for every member ``repeats`` times; report members/sec.

    Excludes data generation and FHIR parsing (measures the engine's compute path).
    """
    members: list[Member] = build_cohort(n, seed)

    # Warm-up (JIT-free Python, but primes caches / imports).
    for m in members[: min(50, len(members))]:
        evaluate_member(m)

    best_rate = 0.0
    per_run: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        for m in members:
            evaluate_member(m)
        elapsed = time.perf_counter() - start
        rate = len(members) / elapsed if elapsed > 0 else 0.0
        per_run.append(rate)
        best_rate = max(best_rate, rate)

    return {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "data_classification": config.SYNTHETIC_TAG,
        "cohort_size": len(members),
        "measures_per_member": 5,
        "repeats": repeats,
        "members_per_sec_best": round(best_rate, 1),
        "members_per_sec_mean": round(sum(per_run) / len(per_run), 1),
        "member_measure_evals_per_sec_best": round(best_rate * 5, 1),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(measure_throughput(), indent=2))
