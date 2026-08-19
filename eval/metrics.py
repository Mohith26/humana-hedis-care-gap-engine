"""Classification metric math (precision / recall / accuracy).

The positive class for care-gap detection is an **open gap**. Metrics are computed
per measure over the members the gold cohort labels for that measure.
"""

from __future__ import annotations

from dataclasses import dataclass

from caregap.measures import STATUS_GAP


@dataclass(frozen=True)
class ConfusionCounts:
    tp: int  # predicted gap, truth gap
    fp: int  # predicted gap, truth not-gap
    fn: int  # predicted not-gap, truth gap
    tn: int  # predicted not-gap, truth not-gap

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def precision(self) -> float | None:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom else None

    @property
    def accuracy(self) -> float | None:
        return ((self.tp + self.tn) / self.total) if self.total else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)


def confusion_from_labels(
    predicted: list[str], truth: list[str], positive: str = STATUS_GAP
) -> ConfusionCounts:
    """Build confusion counts treating ``positive`` as the positive class.

    ``predicted`` and ``truth`` are equal-length lists of status labels
    (e.g. ``not_eligible`` / ``compliant`` / ``gap``). Any label != ``positive``
    is treated as the negative class, so a wrong eligibility call (e.g. predicting a
    gap for a truly not-eligible member) is correctly counted as a false positive.
    """
    if len(predicted) != len(truth):
        raise ValueError("predicted and truth must be the same length")
    tp = fp = fn = tn = 0
    for pred, tru in zip(predicted, truth):
        pred_pos = pred == positive
        true_pos = tru == positive
        if pred_pos and true_pos:
            tp += 1
        elif pred_pos and not true_pos:
            fp += 1
        elif not pred_pos and true_pos:
            fn += 1
        else:
            tn += 1
    return ConfusionCounts(tp=tp, fp=fp, fn=fn, tn=tn)


def exact_match_accuracy(predicted: list[str], truth: list[str]) -> float | None:
    """3-way (not_eligible/compliant/gap) exact-match accuracy."""
    if len(predicted) != len(truth):
        raise ValueError("predicted and truth must be the same length")
    if not truth:
        return None
    correct = sum(1 for p, t in zip(predicted, truth) if p == t)
    return correct / len(truth)
