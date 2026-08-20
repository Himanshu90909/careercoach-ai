from modules.scoring import best_and_worst, normalize_scores, weighted_overall


def test_scores_are_clamped_and_complete():
    scores = normalize_scores({"Confidence": 12, "Flexibility": -4})
    assert scores["Confidence"] == 10.0
    assert scores["Flexibility"] == 0.0
    assert len(scores) == 6


def test_weighted_score_is_reproducible():
    scores = {dimension: 8 for dimension in normalize_scores({})}
    assert weighted_overall(scores) == 8.0


def test_best_and_worst_dimensions():
    scores = {
        "Value justification": 9,
        "Communication clarity": 4,
        "Confidence": 6,
        "Flexibility": 6,
        "Market awareness": 6,
        "Professionalism": 6,
    }
    best, worst = best_and_worst(scores)
    assert best == "Value justification"
    assert worst == "Communication clarity"
