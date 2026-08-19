"""pandas views over engine output (tabular reporting / CSV export)."""

from __future__ import annotations

import pandas as pd

from .engine import population_results
from .measures import MeasureContext
from .model import Member


def population_dataframe(
    members: list[Member], ctx: MeasureContext | None = None
) -> pd.DataFrame:
    """A tidy DataFrame of per-measure denominator/numerator/rate/open_gaps."""
    rows = [
        {
            "measure_id": r.measure_id,
            "name": r.name,
            "denominator": r.denominator,
            "numerator": r.numerator,
            "rate": round(r.rate, 4),
            "open_gaps": r.gaps,
        }
        for r in population_results(members, ctx)
    ]
    return pd.DataFrame(rows, columns=["measure_id", "name", "denominator", "numerator", "rate", "open_gaps"])
