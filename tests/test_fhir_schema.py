"""Optional: validate generated bundles are schema-valid FHIR R4B.

Skips gracefully if ``fhir.resources`` (with an R4B module) is not installed, so the
core suite never hard-depends on it. When present, this proves the seeded generator
emits real, schema-conformant FHIR R4 resources — not ad-hoc JSON.
"""

from __future__ import annotations

import pytest

from datagen.generator import generate_cohort

fhir_r4b = pytest.importorskip("fhir.resources.R4B.bundle", reason="fhir.resources R4B not installed")


def test_generated_bundles_validate_as_fhir_r4b():
    from fhir.resources.R4B.bundle import Bundle

    validated = 0
    for bundle in generate_cohort(25, seed=42):
        Bundle.model_validate(bundle)  # raises on schema violation
        validated += 1
    assert validated == 25
