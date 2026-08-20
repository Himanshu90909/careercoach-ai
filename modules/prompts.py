"""Prompt construction for CareerCoach AI."""

from __future__ import annotations


def scenario_context(scenario: dict) -> str:
    return (
        f"Role: {scenario['role']}\n"
        f"Industry: {scenario['industry']}\n"
        f"Experience: {scenario['experience']}\n"
        f"Work arrangement: {scenario['work_mode']}\n"
        f"Current offer: INR {scenario['current_offer']:,.0f}\n"
        f"Target amount: INR {scenario['target_amount']:,.0f}\n"
        f"Minimum acceptable amount: INR {scenario['minimum_amount']:,.0f}\n"
        f"Negotiation style: {scenario['style']}"
    )


def hr_system_prompt(scenario: dict) -> str:
    return f"""You are CareerCoach AI, a strict but fair HR manager conducting a realistic compensation negotiation simulation.

Scenario:
{scenario_context(scenario)}

Rules:
- Stay in character as an HR manager. Be challenging but respectful.
- Ask one focused question or give one focused counterpoint at a time.
- Do not reveal the candidate's final score during the simulation.
- Challenge unsupported claims and reward specific evidence, measurable outcomes, and thoughtful trade-offs.
- Discuss total compensation and development opportunities when appropriate, but do not invent company policies.
- Treat all amounts as practice values, not financial or employment advice.
- Keep responses under 130 words and end with a clear question or decision point.
"""


def evaluation_prompt(scenario: dict, transcript: str) -> str:
    return f"""Evaluate the following salary negotiation practice session.

Scenario:
{scenario_context(scenario)}

Transcript:
{transcript}

Return only valid JSON with this exact shape:
{{
  "scores": {{
    "Value justification": 0,
    "Communication clarity": 0,
    "Confidence": 0,
    "Flexibility": 0,
    "Market awareness": 0,
    "Professionalism": 0
  }},
  "summary": "Two-sentence summary.",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "missed_opportunities": ["opportunity 1", "opportunity 2"],
  "recommended_phrases": ["phrase 1", "phrase 2", "phrase 3"],
  "seven_day_plan": ["day 1 activity", "day 2 activity", "day 3 activity", "day 4 activity", "day 5 activity", "day 6 activity", "day 7 activity"]
}}

Score every dimension from 0 to 10. Base feedback on the transcript, be specific, and avoid making claims that are not supported by the conversation."""
