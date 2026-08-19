"""Run the engine over the gold cohort and measure per-measure precision/recall/accuracy.

Writes ``results/eval.json``. Every number is produced by an actual run.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from caregap import config
from caregap.engine import default_context
from caregap.fhir_loader import load_member
from caregap.measures import ALL_MEASURES

from datagen.gold_cohort import build_gold_cohort

from .metrics import confusion_from_labels, exact_match_accuracy

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def run_eval() -> dict[str, Any]:
    gold = build_gold_cohort()
    members = [load_member(g.bundle) for g in gold]
    ctx = default_context()

    per_measure: dict[str, Any] = {}
    overall_pred: list[str] = []
    overall_truth: list[str] = []

    for measure in ALL_MEASURES:
        predicted: list[str] = []
        truth: list[str] = []
        for gm, member in zip(gold, members):
            predicted.append(measure.status(member, ctx))
            truth.append(gm.expected[measure.measure_id])
        overall_pred.extend(predicted)
        overall_truth.extend(truth)

        conf = confusion_from_labels(predicted, truth)
        per_measure[measure.measure_id] = {
            "name": measure.name,
            "labeled_members": len(truth),
            "eligible_members": sum(1 for t in truth if t != "not_eligible"),
            "true_gaps": sum(1 for t in truth if t == "gap"),
            "confusion": {"tp": conf.tp, "fp": conf.fp, "fn": conf.fn, "tn": conf.tn},
            "precision": conf.precision,
            "recall": conf.recall,
            "f1": conf.f1,
            "gap_accuracy": conf.accuracy,
            "exact_match_accuracy": exact_match_accuracy(predicted, truth),
        }

    overall_conf = confusion_from_labels(overall_pred, overall_truth)
    result = {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "data_classification": config.SYNTHETIC_TAG,
        "disclaimer": config.DATA_DISCLAIMER,
        "measurement_year": config.MEASUREMENT_YEAR,
        "gold_cohort_members": len(gold),
        "gold_member_measure_evaluations": len(overall_truth),
        "per_measure": per_measure,
        "overall": {
            "confusion": {
                "tp": overall_conf.tp,
                "fp": overall_conf.fp,
                "fn": overall_conf.fn,
                "tn": overall_conf.tn,
            },
            "precision": overall_conf.precision,
            "recall": overall_conf.recall,
            "f1": overall_conf.f1,
            "gap_accuracy": overall_conf.accuracy,
            "exact_match_accuracy": exact_match_accuracy(overall_pred, overall_truth),
        },
    }
    return result


def main() -> None:
    result = run_eval()
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "eval.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    ov = result["overall"]
    print(f"Wrote {out}")
    print(
        f"Overall gap precision={ov['precision']:.4f} recall={ov['recall']:.4f} "
        f"exact-match acc={ov['exact_match_accuracy']:.4f} "
        f"({result['gold_member_measure_evaluations']} evaluations)"
    )


if __name__ == "__main__":
    main()
