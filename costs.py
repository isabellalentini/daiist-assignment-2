"""
Assignment 2: the cost model, shared by train.py and app.py.

Every euro figure and every assumption about the gate lives here, so the cost
sweep that train.py saves and the numbers the dashboard shows always come from
the same place. The reasoning behind each figure is in REPORT.md.

A case is one gate pass (one image). The positive class is "worker without a
hard hat": an image is positive if it has at least one `head` label. The model
gives each image a score, its highest `head` confidence (0 if it found none).

Two thresholds split the score range into three outcomes:

    score <  low            -> pass   (worker walks in)
    low  <= score < high    -> review (snapshot goes to the supervisor)
    score >= high           -> fail   (worker is stopped)

A single threshold is the same thing with low == high, so nothing goes to
review. The test set has about 20% positives, but the gate sees BASE_RATE, so
costs are computed from the rates within each true class and reweighted with
BASE_RATE, never from raw test set counts.
"""

import numpy as np
import pandas as pd

# How often a worker shows up without a hard hat at the gate.
BASE_RATE = 0.03

# Euros per case for each outcome when the model decides alone.
# Placeholders from the framing in REPORT.md, finalised in the cost section.
COST_FP = 1.5   # worker with a hard hat stopped at the gate
COST_FN = 75.0  # worker without a hard hat let onto the site
COST_TP = 0.0   # worker without a hard hat stopped (they would lose this time anyway)
COST_TN = 0.0   # worker with a hard hat walks in

# Human review of a snapshot. Placeholders, finalised in the review section.
REVIEW_SECONDS = 15
SUPERVISOR_HOURLY_EUR = 30.0
REVIEW_COST = REVIEW_SECONDS / 3600 * SUPERVISOR_HOURLY_EUR
REVIEWER_ACCURACY = 1.0  # share of reviewed cases the supervisor gets right

# Gate volume, used to turn shares into people.
CASES_PER_DAY = 600
WORK_SECONDS_PER_DAY = 8 * 3600

THRESHOLDS = np.round(np.linspace(0.0, 1.0, 101), 2)


def outcome_shares(
    scores: np.ndarray, labels: np.ndarray, low: float, high: float
) -> dict[str, float]:
    """Share of positives and of negatives that pass, go to review, or fail."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    high = max(high, low)
    passed = scores < low
    failed = scores >= high
    review = ~passed & ~failed
    pos, neg = labels, ~labels
    return {
        "pos_pass": passed[pos].mean(),
        "pos_review": review[pos].mean(),
        "pos_fail": failed[pos].mean(),
        "neg_pass": passed[neg].mean(),
        "neg_review": review[neg].mean(),
        "neg_fail": failed[neg].mean(),
    }


def outcome_counts(
    scores: np.ndarray, labels: np.ndarray, low: float, high: float
) -> pd.DataFrame:
    """Test set confusion matrix: true class in rows, pass/review/fail in columns."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    high = max(high, low)
    outcome = np.where(scores < low, "pass", np.where(scores >= high, "fail", "review"))
    table = pd.crosstab(
        pd.Series(np.where(labels, "no hard hat", "hard hat"), name="true"),
        pd.Series(outcome, name="decision"),
    )
    return table.reindex(
        index=["no hard hat", "hard hat"], columns=["pass", "review", "fail"], fill_value=0
    )


def cost_per_case(shares: dict[str, float], base_rate: float = BASE_RATE) -> float:
    """Expected euros per gate pass at the gate's base rate.

    A reviewed case costs the supervisor's time, and then the supervisor's
    decision: right with probability REVIEWER_ACCURACY, wrong otherwise.
    """
    right, wrong = REVIEWER_ACCURACY, 1 - REVIEWER_ACCURACY
    positive = (
        shares["pos_pass"] * COST_FN
        + shares["pos_fail"] * COST_TP
        + shares["pos_review"] * (REVIEW_COST + right * COST_TP + wrong * COST_FN)
    )
    negative = (
        shares["neg_pass"] * COST_TN
        + shares["neg_fail"] * COST_FP
        + shares["neg_review"] * (REVIEW_COST + right * COST_TN + wrong * COST_FP)
    )
    return base_rate * positive + (1 - base_rate) * negative


def review_share(shares: dict[str, float], base_rate: float = BASE_RATE) -> float:
    """Share of all gate passes sent to the supervisor, at the gate's base rate."""
    return base_rate * shares["pos_review"] + (1 - base_rate) * shares["neg_review"]


def sweep(
    scores: np.ndarray, labels: np.ndarray, base_rate: float = BASE_RATE
) -> pd.DataFrame:
    """Cost per 1,000 gate passes at every single threshold (no review band)."""
    rows = []
    for t in THRESHOLDS:
        shares = outcome_shares(scores, labels, t, t)
        rows.append({
            "threshold": t,
            "recall": shares["pos_fail"],
            "false_positive_rate": shares["neg_fail"],
            "cost_per_1000": 1000 * cost_per_case(shares, base_rate),
        })
    return pd.DataFrame(rows)
