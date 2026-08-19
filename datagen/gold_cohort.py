"""Hand-built GOLD cohort with KNOWN correct per-measure status (ground truth).

Every member is authored by hand with an explicit expected label per measure
(``not_eligible`` | ``compliant`` | ``gap``) and a scenario note. The cohort covers
the edge cases the spec calls out: age boundaries, out-of-window results, missing
data, poor control, sex ineligibility, and a clinical exclusion (mastectomy).

The engine is then run over these bundles (through the real FHIR loader) and its
output compared to these labels to measure per-measure precision / recall / accuracy.
Because these labels are hand-authored ground truth, a correct engine reproduces them
exactly — this is a correctness/regression eval of the measure logic, not a
generalization benchmark. SYNTHETIC data only — no real PHI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from caregap import codes
from caregap.measures import STATUS_COMPLIANT as C
from caregap.measures import STATUS_GAP as G
from caregap.measures import STATUS_NOT_ELIGIBLE as N

from . import fhir_factory as ff


@dataclass(frozen=True)
class GoldMember:
    member_id: str
    scenario: str
    bundle: dict[str, Any]
    expected: dict[str, str]  # measure_id -> expected status


def _m(
    member_id: str,
    scenario: str,
    *,
    sex: str,
    birth: date,
    resources: list[dict[str, Any]],
    expected: dict[str, str],
    deceased: bool = False,
) -> GoldMember:
    entries = [ff.patient(member_id, sex, birth, deceased)] + resources
    return GoldMember(member_id, scenario, ff.bundle(entries), expected)


def build_gold_cohort() -> list[GoldMember]:
    m: list[GoldMember] = []

    # --- CBP scenarios ---------------------------------------------------
    m.append(_m(
        "gold-01-cbp-controlled", "CBP controlled (BP 128/78 in year); COL colonoscopy in 10yr",
        sex="male", birth=date(1965, 3, 4),
        resources=[
            ff.condition("gold-01-cbp-controlled", "I10", date(2019, 1, 1)),
            ff.bp_observation("gold-01-cbp-controlled", 128, 78, date(2025, 6, 1)),
            ff.procedure("gold-01-cbp-controlled", "45378", date(2019, 5, 2)),
        ],
        expected={"CBP": C, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-02-cbp-uncontrolled", "CBP uncontrolled (last BP 150/95); COL no screen -> gap",
        sex="male", birth=date(1970, 7, 9),
        resources=[
            ff.condition("gold-02-cbp-uncontrolled", "I10", date(2020, 1, 1)),
            ff.bp_observation("gold-02-cbp-uncontrolled", 150, 95, date(2025, 3, 1)),
        ],
        expected={"CBP": G, "GSD": N, "EED": N, "BCS": N, "COL": G},
    ))
    m.append(_m(
        "gold-03-cbp-out-of-window", "CBP BP dated 2024-12 (out of window) -> gap; BCS + COL compliant",
        sex="female", birth=date(1960, 2, 2),
        resources=[
            ff.condition("gold-03-cbp-out-of-window", "I10", date(2018, 1, 1)),
            ff.bp_observation("gold-03-cbp-out-of-window", 130, 80, date(2024, 12, 15)),
            ff.procedure("gold-03-cbp-out-of-window", "77067", date(2024, 5, 1)),   # mammogram
            ff.procedure("gold-03-cbp-out-of-window", "82270", date(2025, 2, 1)),   # FIT
        ],
        expected={"CBP": G, "GSD": N, "EED": N, "BCS": C, "COL": C},
    ))
    m.append(_m(
        "gold-04-cbp-missing", "CBP eligible but NO BP recorded (missing data) -> gap; COL compliant",
        sex="male", birth=date(1980, 8, 8),
        resources=[
            ff.condition("gold-04-cbp-missing", "I10", date(2021, 1, 1)),
            ff.procedure("gold-04-cbp-missing", "45380", date(2025, 4, 1)),
        ],
        expected={"CBP": G, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-05-cbp-age-85", "CBP age boundary 85 (eligible), BP controlled; COL age 85 ineligible",
        sex="male", birth=date(1940, 5, 5),
        resources=[
            ff.condition("gold-05-cbp-age-85", "I10", date(2015, 1, 1)),
            ff.bp_observation("gold-05-cbp-age-85", 135, 85, date(2025, 6, 1)),
        ],
        expected={"CBP": C, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))
    m.append(_m(
        "gold-06-cbp-age-86", "CBP age boundary 86 (INELIGIBLE) despite controlled BP",
        sex="male", birth=date(1939, 5, 5),
        resources=[
            ff.condition("gold-06-cbp-age-86", "I10", date(2015, 1, 1)),
            ff.bp_observation("gold-06-cbp-age-86", 135, 85, date(2025, 6, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))

    # --- GSD / EED scenarios --------------------------------------------
    m.append(_m(
        "gold-07-gsd-controlled", "GSD A1c 6.8 controlled; EED eye exam; COL sigmoidoscopy 5yr",
        sex="male", birth=date(1975, 9, 9),
        resources=[
            ff.condition("gold-07-gsd-controlled", "E11.9", date(2018, 1, 1)),
            ff.a1c_observation("gold-07-gsd-controlled", 6.8, date(2025, 4, 1)),
            ff.procedure("gold-07-gsd-controlled", "92014", date(2025, 5, 1)),
            ff.procedure("gold-07-gsd-controlled", "45330", date(2022, 6, 1)),
        ],
        expected={"CBP": N, "GSD": C, "EED": C, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-08-gsd-uncontrolled", "GSD A1c 8.5 uncontrolled (not poor); EED no exam -> gap; COL no screen -> gap",
        sex="male", birth=date(1978, 10, 10),
        resources=[
            ff.condition("gold-08-gsd-uncontrolled", "E11.9", date(2019, 1, 1)),
            ff.a1c_observation("gold-08-gsd-uncontrolled", 8.5, date(2025, 5, 1)),
        ],
        expected={"CBP": N, "GSD": G, "EED": G, "BCS": N, "COL": G},
    ))
    m.append(_m(
        "gold-09-gsd-poor", "GSD A1c 10.2 poor control -> gap; EED exam compliant; BCS no mammogram -> gap; COL colonoscopy",
        sex="female", birth=date(1968, 3, 3),
        resources=[
            ff.condition("gold-09-gsd-poor", "E11.9", date(2016, 1, 1)),
            ff.a1c_observation("gold-09-gsd-poor", 10.2, date(2025, 7, 1)),
            ff.procedure("gold-09-gsd-poor", "67028", date(2025, 8, 1)),
            ff.procedure("gold-09-gsd-poor", "45384", date(2018, 6, 1)),
        ],
        expected={"CBP": N, "GSD": G, "EED": C, "BCS": G, "COL": C},
    ))
    m.append(_m(
        "gold-10-gsd-missing", "GSD diabetic with NO A1c (missing) -> gap; EED no exam -> gap; COL age 40 ineligible",
        sex="male", birth=date(1985, 11, 11),
        resources=[
            ff.condition("gold-10-gsd-missing", "E10.9", date(2020, 1, 1)),
        ],
        expected={"CBP": N, "GSD": G, "EED": G, "BCS": N, "COL": N},
    ))
    m.append(_m(
        "gold-11-gsd-out-of-window", "GSD A1c dated 2024-11 (out of window) -> gap; EED exam out of window -> gap; COL FIT-DNA 3yr",
        sex="male", birth=date(1972, 12, 12),
        resources=[
            ff.condition("gold-11-gsd-out-of-window", "E11.9", date(2017, 1, 1)),
            ff.a1c_observation("gold-11-gsd-out-of-window", 6.5, date(2024, 11, 1)),
            ff.procedure("gold-11-gsd-out-of-window", "92012", date(2024, 11, 1)),
            ff.procedure("gold-11-gsd-out-of-window", "81528", date(2024, 4, 1)),
        ],
        expected={"CBP": N, "GSD": G, "EED": G, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-12-gsd-age-75", "GSD age boundary 75 (eligible), A1c controlled; EED + COL compliant",
        sex="male", birth=date(1950, 1, 20),
        resources=[
            ff.condition("gold-12-gsd-age-75", "E11.9", date(2010, 1, 1)),
            ff.a1c_observation("gold-12-gsd-age-75", 7.0, date(2025, 3, 1)),
            ff.procedure("gold-12-gsd-age-75", "92014", date(2025, 4, 1)),
            ff.procedure("gold-12-gsd-age-75", "45378", date(2025, 5, 1)),
        ],
        expected={"CBP": N, "GSD": C, "EED": C, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-13-gsd-age-76", "GSD/EED age boundary 76 (INELIGIBLE) despite controlled A1c; COL age 76 ineligible",
        sex="male", birth=date(1949, 1, 20),
        resources=[
            ff.condition("gold-13-gsd-age-76", "E11.9", date(2010, 1, 1)),
            ff.a1c_observation("gold-13-gsd-age-76", 7.0, date(2025, 3, 1)),
            ff.procedure("gold-13-gsd-age-76", "92014", date(2025, 4, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))

    # --- BCS scenarios ---------------------------------------------------
    m.append(_m(
        "gold-14-bcs-compliant", "BCS mammogram in year (compliant); COL CT colonography 5yr",
        sex="female", birth=date(1965, 4, 4),
        resources=[
            ff.procedure("gold-14-bcs-compliant", "77067", date(2025, 3, 1)),
            ff.procedure("gold-14-bcs-compliant", "74263", date(2023, 7, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": C, "COL": C},
    ))
    m.append(_m(
        "gold-15-bcs-missing", "BCS no mammogram (missing) -> gap; COL no screen -> gap",
        sex="female", birth=date(1960, 6, 6),
        resources=[],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": G, "COL": G},
    ))
    m.append(_m(
        "gold-16-bcs-out-of-window", "BCS mammogram 2023-06 before Oct-1 window start -> gap; COL FIT compliant",
        sex="female", birth=date(1958, 2, 6),
        resources=[
            ff.procedure("gold-16-bcs-out-of-window", "77067", date(2023, 6, 1)),
            ff.procedure("gold-16-bcs-out-of-window", "82274", date(2025, 1, 15)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": G, "COL": C},
    ))
    m.append(_m(
        "gold-17-bcs-age-74", "BCS age boundary 74 (eligible), mammogram compliant; COL colonoscopy",
        sex="female", birth=date(1951, 3, 15),
        resources=[
            ff.procedure("gold-17-bcs-age-74", "77066", date(2025, 5, 1)),
            ff.procedure("gold-17-bcs-age-74", "45380", date(2020, 5, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": C, "COL": C},
    ))
    m.append(_m(
        "gold-18-bcs-age-75", "BCS age boundary 75 (INELIGIBLE) despite mammogram; COL compliant",
        sex="female", birth=date(1950, 3, 15),
        resources=[
            ff.procedure("gold-18-bcs-age-75", "77067", date(2025, 5, 1)),
            ff.procedure("gold-18-bcs-age-75", "45378", date(2025, 6, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-19-bcs-mastectomy", "BCS bilateral mastectomy EXCLUSION -> ineligible; COL no screen -> gap",
        sex="female", birth=date(1962, 7, 7),
        resources=[
            ff.procedure("gold-19-bcs-mastectomy", "19303", date(2020, 1, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": G},
    ))
    m.append(_m(
        "gold-20-bcs-male", "BCS male -> ineligible (sex); COL flex sigmoidoscopy 5yr compliant",
        sex="male", birth=date(1960, 9, 9),
        resources=[
            ff.procedure("gold-20-bcs-male", "45331", date(2021, 6, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))

    # --- COL scenarios ---------------------------------------------------
    m.append(_m(
        "gold-21-col-out-of-window", "COL colonoscopy 2015-06 before 10yr window -> gap",
        sex="male", birth=date(1970, 4, 4),
        resources=[
            ff.procedure("gold-21-col-out-of-window", "45378", date(2015, 6, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": G},
    ))
    m.append(_m(
        "gold-22-col-lab-fit", "COL FIT as LOINC-coded lab Observation (compliant); BCS age 46 ineligible",
        sex="female", birth=date(1979, 5, 5),
        resources=[
            ff.lab_observation("gold-22-col-lab-fit", "2335-8", date(2025, 2, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-23-col-age-45", "COL age boundary 45 (eligible), colonoscopy compliant",
        sex="male", birth=date(1980, 6, 6),
        resources=[
            ff.procedure("gold-23-col-age-45", "45378", date(2025, 1, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": C},
    ))
    m.append(_m(
        "gold-24-col-age-44", "COL age boundary 44 (INELIGIBLE) despite colonoscopy",
        sex="male", birth=date(1981, 6, 6),
        resources=[
            ff.procedure("gold-24-col-age-44", "45378", date(2025, 1, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))

    # --- negative controls ----------------------------------------------
    m.append(_m(
        "gold-25-healthy-young", "Healthy 30yo, no conditions -> ineligible for every measure",
        sex="male", birth=date(1995, 5, 5),
        resources=[],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))
    m.append(_m(
        "gold-26-deceased", "Deceased member with uncontrolled conditions -> excluded from all measures",
        sex="male", birth=date(1960, 5, 5), deceased=True,
        resources=[
            ff.condition("gold-26-deceased", "I10", date(2015, 1, 1)),
            ff.condition("gold-26-deceased", "E11.9", date(2015, 1, 1)),
            ff.bp_observation("gold-26-deceased", 160, 100, date(2025, 6, 1)),
            ff.a1c_observation("gold-26-deceased", 10.0, date(2025, 6, 1)),
        ],
        expected={"CBP": N, "GSD": N, "EED": N, "BCS": N, "COL": N},
    ))

    return m


# Sanity: keep the code-set import referenced so unused-import linters stay quiet and
# so a broken code-set constant surfaces at import time.
_ = codes.MAMMOGRAM_CODES
