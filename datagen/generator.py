"""Seeded synthetic FHIR R4 cohort generator (documented fallback for Synthea).

Why a seeded generator and not Synthea's Java pipeline: this environment has no Java
runtime, and a fully deterministic, dependency-free generator gives exact control over
the population and reproduces byte-identically from a seed. The output is FHIR R4
Bundle JSON shaped like Synthea's (Patient/Condition/Observation/Procedure) so the
same loader handles both. **All data is SYNTHETIC — no real PHI.**

Distributions are illustrative (a plausible Medicare-Advantage skew), not calibrated
to any real population; population rates are therefore emergent artifacts of these
knobs, reported honestly as such.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from caregap import codes, config

from . import fhir_factory as ff

MY = config.MEASUREMENT_YEAR
YEAR_START = config.MEASUREMENT_YEAR_START
YEAR_END = config.MEASUREMENT_YEAR_END

# Prevalence / performance knobs (SYNTHETIC — illustrative only).
P_HYPERTENSION = 0.35
P_DIABETES = 0.16
P_DECEASED = 0.01

P_BP_IN_YEAR = 0.85          # hypertensives with a BP reading in the measurement year
P_BP_CONTROLLED = 0.62       # of those readings, fraction < 140/90
P_BP_ONLY_STALE = 0.06       # hypertensives whose only BP is before the year (out-of-window)

P_A1C_IN_YEAR = 0.80         # diabetics with an A1c in the measurement year
P_A1C_CONTROLLED = 0.60      # of those, fraction < 8.0%
P_A1C_POOR = 0.18            # of those, fraction > 9.0% (subset of not-controlled)
P_EYE_EXAM = 0.63            # diabetics with a diabetic eye exam in the year

P_MAMMOGRAM = 0.70           # eligible women with a mammogram in the look-back window
P_COL_SCREEN = 0.65          # 45-75 members with a colorectal screen in a valid window


def _random_birth_date(rng: random.Random, age: int) -> date:
    """Birth date such that age as of Dec 31 of the measurement year == ``age``."""
    year = MY - age
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return date(year, month, day)


def _draw_age(rng: random.Random) -> int:
    bucket = rng.random()
    if bucket < 0.40:
        return rng.randint(65, 85)
    if bucket < 0.70:
        return rng.randint(50, 64)
    if bucket < 0.90:
        return rng.randint(40, 49)
    return rng.randint(18, 39)


def _day_in_year(rng: random.Random) -> date:
    return YEAR_START + timedelta(days=rng.randint(0, 364))


def generate_member_bundle(rng: random.Random, index: int) -> dict[str, Any]:
    member_id = f"syn-{index:05d}"
    age = _draw_age(rng)
    gender = "female" if rng.random() < 0.5 else "male"
    deceased = rng.random() < P_DECEASED
    birth = _random_birth_date(rng, age)

    resources: list[dict[str, Any]] = [ff.patient(member_id, gender, birth, deceased)]

    has_htn = rng.random() < P_HYPERTENSION
    has_dm = rng.random() < P_DIABETES

    if has_htn:
        resources.append(
            ff.condition(member_id, "I10", onset=date(MY - rng.randint(1, 8), 1, 1))
        )
        roll = rng.random()
        if roll < P_BP_ONLY_STALE:
            # Only an out-of-window (prior-year) reading -> should be an open gap.
            stale = date(MY - 1, rng.randint(1, 11), rng.randint(1, 28))
            resources.append(ff.bp_observation(member_id, rng.randint(120, 150), rng.randint(75, 95), stale))
        elif roll < P_BP_IN_YEAR:
            if rng.random() < P_BP_CONTROLLED:
                sys_v, dia_v = rng.randint(110, 138), rng.randint(65, 88)
            else:
                sys_v, dia_v = rng.randint(141, 175), rng.randint(88, 105)
            resources.append(ff.bp_observation(member_id, sys_v, dia_v, _day_in_year(rng)))
        # else: no BP at all -> open gap (missing data)

    if has_dm:
        dm_code = "E11.9" if rng.random() < 0.85 else "E10.9"
        resources.append(
            ff.condition(member_id, dm_code, onset=date(MY - rng.randint(1, 10), 1, 1))
        )
        if rng.random() < P_A1C_IN_YEAR:
            r = rng.random()
            if r < P_A1C_CONTROLLED:
                value = round(rng.uniform(5.5, 7.9), 1)
            elif r < P_A1C_CONTROLLED + P_A1C_POOR:
                value = round(rng.uniform(9.1, 12.0), 1)   # poor control
            else:
                value = round(rng.uniform(8.0, 9.0), 1)    # not controlled, not "poor"
            resources.append(ff.a1c_observation(member_id, value, _day_in_year(rng)))
        # else: no A1c -> open gap (missing data)

        if rng.random() < P_EYE_EXAM:
            exam_code = rng.choice(sorted(codes.EYE_EXAM_CODES))
            resources.append(ff.procedure(member_id, exam_code, _day_in_year(rng)))

    # BCS — women 50-74.
    if gender == "female" and 50 <= age <= 74 and rng.random() < P_MAMMOGRAM:
        # anywhere in the 27-month look-back window
        start = date(MY - 2, 10, 1)
        span = (YEAR_END - start).days
        when = start + timedelta(days=rng.randint(0, span))
        resources.append(ff.procedure(member_id, rng.choice(sorted(codes.MAMMOGRAM_CODES)), when))

    # COL — 45-75, pick a modality and place it inside its valid window.
    if 45 <= age <= 75 and rng.random() < P_COL_SCREEN:
        modality = rng.choice(["colonoscopy", "fit", "fit_dna", "sigmoidoscopy", "ct"])
        if modality == "colonoscopy":
            when = date(MY - rng.randint(0, 9), rng.randint(1, 12), rng.randint(1, 28))
            resources.append(ff.procedure(member_id, rng.choice(sorted(codes.COLONOSCOPY_CODES)), when))
        elif modality == "fit":
            resources.append(ff.procedure(member_id, rng.choice(sorted(codes.FIT_FOBT_CODES)), _day_in_year(rng)))
        elif modality == "fit_dna":
            when = date(MY - rng.randint(0, 2), rng.randint(1, 12), rng.randint(1, 28))
            resources.append(ff.procedure(member_id, "81528", when))
        elif modality == "sigmoidoscopy":
            when = date(MY - rng.randint(0, 4), rng.randint(1, 12), rng.randint(1, 28))
            resources.append(ff.procedure(member_id, rng.choice(sorted(codes.FLEX_SIGMOIDOSCOPY_CODES)), when))
        else:  # ct colonography
            when = date(MY - rng.randint(0, 4), rng.randint(1, 12), rng.randint(1, 28))
            resources.append(ff.procedure(member_id, "74263", when))

    return ff.bundle(resources)


def generate_cohort(n: int, seed: int = 42) -> list[dict[str, Any]]:
    """Generate ``n`` synthetic member FHIR bundles deterministically from ``seed``."""
    rng = random.Random(seed)
    return [generate_member_bundle(rng, i) for i in range(n)]
