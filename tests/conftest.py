"""Shared fixtures."""

from __future__ import annotations

import pytest

from caregap.engine import default_context
from caregap.fhir_loader import load_member
from caregap.store import MemberStore

from datagen.gold_cohort import build_gold_cohort


@pytest.fixture(scope="session")
def ctx():
    return default_context()


@pytest.fixture(scope="session")
def gold():
    """The hand-built gold cohort: list of GoldMember (bundle + expected labels)."""
    return build_gold_cohort()


@pytest.fixture(scope="session")
def gold_members(gold):
    """Gold members parsed through the real FHIR loader, paired with their GoldMember."""
    return [(gm, load_member(gm.bundle)) for gm in gold]


@pytest.fixture(scope="session")
def gold_store(gold):
    return MemberStore([load_member(gm.bundle) for gm in gold])
