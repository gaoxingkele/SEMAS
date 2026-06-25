"""Alpha decay monitoring utilities.

Tracks how a factor's predictive power evolves over time and generations,
allowing the loop to trigger re-evolution when IC decays.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_ic_decay(history: list[dict[str, Any]], window: int = 3) -> float:
    """Return the slope of best_test_ic over the last `window` generations.

    A negative slope indicates alpha decay.
    """
    if len(history) < window:
        return 0.0
    recent = history[-window:]
    x = np.arange(len(recent))
    y = np.array([g["best_test_ic"] for g in recent])
    if np.isnan(y).any():
        return 0.0
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def compute_overfit_ratio(
    candidate,
) -> float:
    """Ratio of train-vs-test IC gap relative to train IC."""
    train_ic = getattr(candidate, "train_ic", 0.0)
    test_ic = getattr(candidate, "test_ic", 0.0)
    if abs(train_ic) < 1e-8:
        return 0.0
    return (train_ic - test_ic) / abs(train_ic)


def decay_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a human-readable decay summary."""
    if not history:
        return {}
    decay_3 = compute_ic_decay(history, window=3)
    decay_5 = compute_ic_decay(history, window=5)
    return {
        "latest_best_test_ic": history[-1]["best_test_ic"],
        "ic_decay_slope_3gen": decay_3,
        "ic_decay_slope_5gen": decay_5,
        "decaying": bool(decay_3 < -0.005),
    }
