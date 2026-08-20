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


def role_match_prompt(resume_text: str, job_text: str) -> str:
    return f"""Compare this candidate resume with the internship description.

Resume:
{resume_text}

Internship description:
{job_text}

Return only valid JSON with this shape:
{{
  "match_score": 0,
  "role_summary": "one sentence",
  "matched_skills": ["skill"],
  "missing_skills": ["skill"],
  "evidence": ["resume evidence connected to a requirement"],
  "questions": [
    {{"question": "role-specific interview question", "why_it_matters": "short reason", "ideal_points": ["point"]}}
  ],
  "study_plan": ["action"]
}}
Use only evidence present in the resume. Generate 6 to 10 questions, prioritizing the internship requirements and the candidate's gaps."""


def tailored_response_prompt(context: dict, question: str, answer: str) -> str:
    return f"""You are a practical internship interview coach.

Role summary: {context.get('role_summary', '')}
Matched skills: {', '.join(context.get('matched_skills', []))}
Missing skills: {', '.join(context.get('missing_skills', []))}
Question: {question}
Candidate answer: {answer}

Give concise feedback in this structure:
1. Score out of 10.
2. What was strong.
3. What was missing or unclear.
4. A stronger STAR-style answer outline.
5. One follow-up question.
Keep it supportive, specific, and under 180 words."""


def interview_question_prompt(role: str, description: str, topics: list[str], candidate_context: str) -> str:
    return f"""Create a comprehensive interview practice bank for any person preparing for this role.

Role: {role}
Role or internship description: {description}
Topics: {', '.join(topics)}
Candidate context: {candidate_context or 'Not provided'}

Return only valid JSON:
{{
  "role_summary": "one sentence",
  "questions": [
    {{"topic": "topic", "difficulty": "Beginner|Intermediate|Advanced", "question": "question", "ideal_points": ["point"]}}
  ],
  "skill_rubric": ["skill to evaluate"],
  "coding_focus": ["coding topic"]
}}
Generate at least 10 questions across the selected topics. Include technical, behavioral, project, and role-specific questions when relevant. Do not invent facts about the candidate."""


def interview_assistant_prompt(role: str, context: str, history: str, user_message: str) -> str:
    return f"""You are an AI interview assistant for the role: {role}.

Candidate and role context:
{context}

Conversation:
{history}

Candidate message:
{user_message}

Answer helpfully. You may explain concepts, ask a mock interview question, provide hints, critique an answer, or suggest a study step. Keep the answer concise and end with one actionable next step."""


def answer_evaluation_prompt(role: str, question: str, answer: str, rubric: list[str]) -> str:
    return f"""Evaluate this interview answer for the role {role}.
Question: {question}
Answer: {answer}
Skills to assess: {', '.join(rubric)}

Return only valid JSON:
{{
  "score": 0,
  "skill_scores": {{"skill": 0}},
  "strengths": ["strength"],
  "improvements": ["improvement"],
  "model_answer_outline": ["STAR or technical reasoning point"],
  "follow_up": "one follow-up question"
}}
Use a 0-10 score and assess only evidence in the answer."""


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
