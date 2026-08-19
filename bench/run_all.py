"""Run every benchmark + the correctness eval and (re)write results/*.json + summary.

All numbers come from an actual run on SYNTHETIC seeded data.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from caregap import config

from eval.run_eval import run_eval

from .common import DEFAULT_COHORT_SIZE, DEFAULT_SEED
from .latency import measure_latency
from .population import population_report
from .throughput import measure_throughput

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _write(name: str, payload: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_all(n: int = DEFAULT_COHORT_SIZE, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    eval_result = run_eval()
    population = population_report(n, seed)
    throughput = measure_throughput(n, seed)
    latency = measure_latency(n, seed)

    _write("eval.json", eval_result)
    _write("population.json", population)
    _write("throughput.json", throughput)
    _write("latency.json", latency)

    summary = {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "data_classification": config.SYNTHETIC_TAG,
        "disclaimer": config.DATA_DISCLAIMER,
        "measurement_year": config.MEASUREMENT_YEAR,
        "cohort_size": population["cohort_size"],
        "fhir_resources": population["fhir_resources"],
        "seed": seed,
        "gold_cohort": {
            "members": eval_result["gold_cohort_members"],
            "evaluations": eval_result["gold_member_measure_evaluations"],
            "overall_gap_precision": eval_result["overall"]["precision"],
            "overall_gap_recall": eval_result["overall"]["recall"],
            "overall_exact_match_accuracy": eval_result["overall"]["exact_match_accuracy"],
            "per_measure": {
                mid: {
                    "precision": v["precision"],
                    "recall": v["recall"],
                    "gap_accuracy": v["gap_accuracy"],
                    "exact_match_accuracy": v["exact_match_accuracy"],
                }
                for mid, v in eval_result["per_measure"].items()
            },
        },
        "population": {
            m["measure_id"]: {
                "denominator": m["denominator"],
                "numerator": m["numerator"],
                "rate": m["rate"],
                "open_gaps": m["open_gaps"],
            }
            for m in population["measures"]
        },
        "total_open_gaps": population["total_open_gaps"],
        "members_with_any_gap": population["members_with_any_gap"],
        "throughput_members_per_sec": throughput["members_per_sec_best"],
        "latency": {
            "measures_p50_ms": latency["measures_endpoint"]["p50_ms"],
            "measures_p95_ms": latency["measures_endpoint"]["p95_ms"],
            "care_gaps_p50_ms": latency["care_gaps_endpoint"]["p50_ms"],
            "care_gaps_p95_ms": latency["care_gaps_endpoint"]["p95_ms"],
        },
    }
    _write("summary.json", summary)
    return summary


def main() -> None:
    summary = run_all()
    print(f"Wrote results/*.json to {RESULTS_DIR}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
