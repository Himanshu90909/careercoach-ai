"""Local, deterministic scoring helpers for CareerCoach AI."""

from __future__ import annotations

from typing import Any

DIMENSIONS = [
    "Value justification",
    "Communication clarity",
    "Confidence",
    "Flexibility",
    "Market awareness",
    "Professionalism",
]

WEIGHTS = {
    "Value justification": 0.22,
    "Communication clarity": 0.18,
    "Confidence": 0.18,
    "Flexibility": 0.14,
    "Market awareness": 0.16,
    "Professionalism": 0.12,
}


def clamp_score(value: Any) -> float:
    """Convert an arbitrary value into a score between 0 and 10."""
    try:
        return max(0.0, min(10.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def normalize_scores(scores: dict[str, Any] | None) -> dict[str, float]:
    scores = scores or {}
    return {dimension: round(clamp_score(scores.get(dimension, 0)), 1) for dimension in DIMENSIONS}


def weighted_overall(scores: dict[str, Any] | None) -> float:
    normalized = normalize_scores(scores)
    return round(sum(normalized[key] * WEIGHTS[key] for key in DIMENSIONS), 1)


def improvement_delta(history: list[float]) -> float:
    if len(history) < 2:
        return 0.0
    return round(history[-1] - history[0], 1)


def best_and_worst(scores: dict[str, Any] | None) -> tuple[str, str]:
    normalized = normalize_scores(scores)
    if not normalized:
        return "Not available", "Not available"
    return max(normalized, key=normalized.get), min(normalized, key=normalized.get)
