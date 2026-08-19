"""Central configuration: measurement year, thresholds, Stars weights, SYNTHETIC tag.

All numbers here are HEDIS-STYLE / simplified — NOT NCQA-certified. Every value is a
named constant so measure logic never hides a magic number.
"""

from __future__ import annotations

from datetime import date

# ---------------------------------------------------------------------------
# Data provenance — this project NEVER uses real PHI. All data is SYNTHETIC.
# ---------------------------------------------------------------------------
SYNTHETIC_TAG: str = "SYNTHETIC"
DATA_DISCLAIMER: str = (
    "SYNTHETIC data only — deterministically generated, no real Protected Health "
    "Information (PHI). HEDIS-style measure logic is simplified and NOT NCQA-certified."
)

# ---------------------------------------------------------------------------
# Measurement year and derived window boundaries.
# HEDIS convention used here: member age is evaluated as of December 31 of the
# measurement year, and the "measurement year" window is the full calendar year.
# ---------------------------------------------------------------------------
MEASUREMENT_YEAR: int = 2025
MEASUREMENT_YEAR_START: date = date(MEASUREMENT_YEAR, 1, 1)
MEASUREMENT_YEAR_END: date = date(MEASUREMENT_YEAR, 12, 31)

# ---------------------------------------------------------------------------
# Clinical thresholds (HEDIS-style / simplified).
# ---------------------------------------------------------------------------
# CBP — Controlling High Blood Pressure: controlled if most-recent BP < 140/90.
CBP_SYSTOLIC_THRESHOLD: int = 140  # mmHg; compliant requires systolic < this
CBP_DIASTOLIC_THRESHOLD: int = 90  # mmHg; compliant requires diastolic < this

# GSD — Glycemic Status (HbA1c) control: compliant if most-recent A1c < 8.0%.
GSD_A1C_CONTROL_THRESHOLD: float = 8.0   # % ; compliant requires A1c < this
GSD_A1C_POOR_CONTROL_THRESHOLD: float = 9.0  # % ; A1c > this flagged poor control

# ---------------------------------------------------------------------------
# Stars measure weights (outreach prioritization).
# CMS triple-weights outcome/intermediate-outcome measures; process measures = 1x.
# Used ONLY to rank the outreach worklist (gap_count-weighted). HEDIS-style.
# ---------------------------------------------------------------------------
MEASURE_WEIGHTS: dict[str, float] = {
    "CBP": 3.0,  # intermediate outcome (BP control) — triple weighted
    "GSD": 3.0,  # intermediate outcome (A1c control) — triple weighted
    "EED": 1.0,  # process measure
    "BCS": 1.0,  # process measure
    "COL": 1.0,  # process measure
}
DEFAULT_MEASURE_WEIGHT: float = 1.0
