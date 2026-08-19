"""Population measure rates + gap totals over the full synthetic cohort."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from caregap import config
from caregap.engine import population_results
from caregap.fhir_loader import count_resources
from caregap.gaps import all_gaps, members_with_any_gap
from caregap.model import Member

from datagen.generator import generate_cohort

from .common import DEFAULT_COHORT_SIZE, DEFAULT_SEED, build_cohort


def population_report(
    n: int = DEFAULT_COHORT_SIZE, seed: int = DEFAULT_SEED
) -> dict[str, Any]:
    bundles = generate_cohort(n, seed)
    n_resources = count_resources(bundles)
    members: list[Member] = build_cohort(n, seed)

    results = population_results(members)
    gaps = all_gaps(members)

    measures = [
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

    return {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "data_classification": config.SYNTHETIC_TAG,
        "disclaimer": config.DATA_DISCLAIMER,
        "measurement_year": config.MEASUREMENT_YEAR,
        "seed": seed,
        "cohort_size": len(members),
        "fhir_resources": n_resources,
        "measures": measures,
        "total_open_gaps": len(gaps),
        "members_with_any_gap": members_with_any_gap(members),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(population_report(), indent=2))
