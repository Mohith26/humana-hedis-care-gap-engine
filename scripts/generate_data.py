"""Generate the SYNTHETIC FHIR cohort to disk (and a small committed sample).

Usage:
    python -m scripts.generate_data --n 1000 --seed 42

Writes one FHIR R4 Bundle JSON per member into ``data/synthetic_fhir/`` (gitignored),
and refreshes a handful of example bundles under ``samples/`` (committed) so the repo
carries runnable examples without a huge data dump. SYNTHETIC data only — no PHI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datagen.generator import generate_cohort

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "synthetic_fhir"
SAMPLE_DIR = ROOT / "samples"
SAMPLE_COUNT = 5


def _member_id(bundle: dict) -> str:
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        if res.get("resourceType") == "Patient":
            return str(res.get("id"))
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic FHIR cohort (no PHI).")
    parser.add_argument("--n", type=int, default=1000, help="number of members")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (reproducible)")
    args = parser.parse_args()

    bundles = generate_cohort(args.n, args.seed)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for existing in DATA_DIR.glob("*.json"):
        existing.unlink()
    for bundle in bundles:
        mid = _member_id(bundle)
        (DATA_DIR / f"{mid}.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    SAMPLE_DIR.mkdir(exist_ok=True)
    for existing in SAMPLE_DIR.glob("*.json"):
        existing.unlink()
    for bundle in bundles[:SAMPLE_COUNT]:
        mid = _member_id(bundle)
        (SAMPLE_DIR / f"{mid}.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(bundles)} SYNTHETIC member bundles to {DATA_DIR}")
    print(f"Wrote {min(SAMPLE_COUNT, len(bundles))} sample bundles to {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
