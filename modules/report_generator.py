"""Build a readable Markdown report from a completed session."""

from __future__ import annotations

from datetime import datetime

from .scoring import normalize_scores, weighted_overall


def build_report(scenario: dict, evaluation: dict, transcript: list[dict[str, str]]) -> str:
    scores = normalize_scores(evaluation.get("scores"))
    lines = [
        "# CareerCoach AI — Negotiation Coaching Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Scenario",
        "",
        f"- **Role:** {scenario['role']}",
        f"- **Industry:** {scenario['industry']}",
        f"- **Experience:** {scenario['experience']}",
        f"- **Current offer:** INR {scenario['current_offer']:,.0f}",
        f"- **Target amount:** INR {scenario['target_amount']:,.0f}",
        "",
        "## Overall Result",
        "",
        f"**Weighted score: {weighted_overall(scores):.1f}/10**",
        "",
        evaluation.get("summary", "No summary was returned."),
        "",
        "## Scorecard",
        "",
        "| Dimension | Score |\n|---|---:|",
    ]
    lines.extend(f"| {dimension} | {scores[dimension]:.1f}/10 |" for dimension in scores)
    for title, key in [("Strengths", "strengths"), ("Development areas", "weaknesses"), ("Missed opportunities", "missed_opportunities"), ("Recommended phrases", "recommended_phrases"), ("Seven-day practice plan", "seven_day_plan")]:
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"{index}. {item}" for index, item in enumerate(evaluation.get(key, []), 1))
    lines.extend(["", "## Conversation Transcript", "", "| Speaker | Message |", "|---|---|"])
    lines.extend(f"| {item['speaker']} | {item['text'].replace('|', '\\|')} |" for item in transcript)
    lines.extend(["", "---", "", "This report is for practice and educational purposes. It is not financial, legal, or employment advice."])
    return "\n".join(lines)
