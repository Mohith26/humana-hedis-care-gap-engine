"""pandas tabular view + file-backed MemberStore loading."""

from __future__ import annotations

import json
from datetime import date

from caregap.store import MemberStore
from caregap.tabular import population_dataframe

from datagen import fhir_factory as ff
from datagen.generator import generate_cohort


def test_population_dataframe_shape_and_columns():
    members = MemberStore.from_bundles(generate_cohort(100, seed=42)).members
    df = population_dataframe(members)
    assert list(df.columns) == ["measure_id", "name", "denominator", "numerator", "rate", "open_gaps"]
    assert set(df["measure_id"]) == {"CBP", "GSD", "EED", "BCS", "COL"}
    assert (df["rate"] >= 0).all() and (df["rate"] <= 1).all()
    # numerator + open_gaps == denominator for every measure
    assert ((df["numerator"] + df["open_gaps"]) == df["denominator"]).all()


def test_store_from_bundle_dir(tmp_path):
    bundles = generate_cohort(10, seed=42)
    for i, b in enumerate(bundles):
        (tmp_path / f"m{i:03d}.json").write_text(json.dumps(b), encoding="utf-8")
    store = MemberStore.from_bundle_dir(tmp_path)
    assert len(store) == 10
    assert store.get(store.ids()[0]) is not None
    assert store.get("missing") is None


def test_store_get_and_ids():
    b = ff.bundle([ff.patient("px", "female", date(1970, 1, 1))])
    store = MemberStore.from_bundles([b])
    assert store.ids() == ["px"]
    assert store.get("px").sex == "female"
