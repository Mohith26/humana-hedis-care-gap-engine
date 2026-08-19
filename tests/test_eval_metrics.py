"""Precision / recall / accuracy math + the gold-cohort eval run."""

from __future__ import annotations

from eval.metrics import confusion_from_labels, exact_match_accuracy
from eval.run_eval import run_eval

GAP = "gap"
COMP = "compliant"
NE = "not_eligible"


def test_confusion_counts_basic():
    pred = [GAP, GAP, COMP, COMP, GAP]
    truth = [GAP, COMP, COMP, GAP, GAP]
    c = confusion_from_labels(pred, truth)
    # index: (gap,gap)=TP, (gap,comp)=FP, (comp,comp)=TN, (comp,gap)=FN, (gap,gap)=TP
    assert (c.tp, c.fp, c.fn, c.tn) == (2, 1, 1, 1)
    assert c.precision == 2 / 3
    assert c.recall == 2 / 3
    assert c.accuracy == 3 / 5


def test_not_eligible_misprediction_counts_as_fp():
    # Predicting a gap for a truly not-eligible member is a false positive.
    c = confusion_from_labels([GAP], [NE])
    assert (c.tp, c.fp, c.fn, c.tn) == (0, 1, 0, 0)


def test_perfect_prediction():
    pred = [GAP, COMP, NE]
    c = confusion_from_labels(pred, pred)
    assert c.precision == 1.0
    assert c.recall == 1.0
    assert c.accuracy == 1.0
    assert exact_match_accuracy(pred, pred) == 1.0


def test_precision_none_when_no_positive_predictions():
    c = confusion_from_labels([COMP, NE], [GAP, COMP])
    assert c.precision is None  # no predicted positives
    assert c.recall == 0.0


def test_f1_harmonic_mean():
    c = confusion_from_labels([GAP, GAP, COMP], [GAP, COMP, GAP])
    # tp=1, fp=1, fn=1 -> p=0.5, r=0.5, f1=0.5
    assert c.f1 == 0.5


def test_run_eval_reproduces_gold_truth_exactly():
    """The engine must reproduce the hand-labeled gold cohort (a correctness eval)."""
    result = run_eval()
    overall = result["overall"]
    assert overall["exact_match_accuracy"] == 1.0
    assert overall["precision"] == 1.0
    assert overall["recall"] == 1.0
    for mid, stats in result["per_measure"].items():
        assert stats["precision"] == 1.0, f"{mid} precision"
        assert stats["recall"] == 1.0, f"{mid} recall"
        assert stats["exact_match_accuracy"] == 1.0, f"{mid} exact-match"
        assert stats["true_gaps"] >= 1, f"{mid} should have >=1 true gap"
