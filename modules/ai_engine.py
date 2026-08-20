"""Gemini integration with deterministic demo fallbacks."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

from .prompts import (answer_evaluation_prompt, evaluation_prompt, hr_system_prompt, interview_assistant_prompt, interview_question_prompt, role_match_prompt, tailored_response_prompt)
from .scoring import DIMENSIONS

try:
    from google import genai
except ImportError:  # pragma: no cover - handled by requirements.txt
    genai = None


class AIEngine:
    """Provider-neutral AI boundary for Gemini, Grok, and deterministic demo mode."""

    def __init__(self, provider: str = "demo", api_key: str = "", model: str = "") -> None:
        self.provider = provider.lower().strip() or "demo"
        self.api_key = api_key.strip()
        self.last_error = ""
        self.model = model.strip() or ({"gemini": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), "grok": os.getenv("GROK_MODEL", "grok-4.6")}.get(self.provider, "demo"))
        self.client = genai.Client(api_key=self.api_key) if genai and self.provider == "gemini" and self.api_key else None

    @property
    def available(self) -> bool:
        return (self.client is not None) if self.provider == "gemini" else bool(self.provider == "grok" and self.api_key)

    @property
    def label(self) -> str:
        return {"gemini": "Gemini", "grok": "Grok", "demo": "Demo mode"}.get(self.provider, "Demo mode")

    def _generate(self, prompt: str, system_instruction: str = "") -> str:
        self.last_error = ""
        if self.provider == "gemini":
            if not self.client:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"system_instruction": system_instruction, "temperature": 0.7},
            )
            return (response.text or "").strip()
        if self.provider == "grok":
            if not self.api_key:
                raise RuntimeError("GROK_API_KEY is not configured")
            response = requests.post(
                os.getenv("GROK_BASE_URL", "https://api.x.ai/v1") + "/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}], "temperature": 0.7},
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            return (payload.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        raise RuntimeError("Demo mode uses deterministic local fallbacks")

    def _record_error(self, exc: Exception) -> None:
        message = str(exc).replace(self.api_key, "[REDACTED]")
        self.last_error = message[:300] or exc.__class__.__name__

    def hr_response(self, scenario: dict, transcript: list[dict[str, str]]) -> str:
        context = "\n".join(f"{item['speaker']}: {item['text']}" for item in transcript[-8:])
        prompt = f"Conversation so far:\n{context}\n\nRespond as the HR manager for the next round."
        try:
            return self._generate(prompt, hr_system_prompt(scenario))
        except Exception as exc:
            self._record_error(exc)
            return self.demo_hr_response(scenario, len(transcript))

    def match_resume_to_role(self, resume_text: str, job_text: str) -> dict[str, Any]:
        try:
            raw = self._generate(role_match_prompt(resume_text, job_text), "You are a precise internship recruiting analyst.")
            parsed = self._parse_json(raw)
            if parsed and isinstance(parsed.get("questions"), list):
                return parsed
        except Exception as exc:
            self._record_error(exc)
        return self.demo_role_match(resume_text, job_text)

    def coach_answer(self, context: dict[str, Any], question: str, answer: str) -> str:
        try:
            return self._generate(tailored_response_prompt(context, question, answer), "You are a supportive but rigorous interview coach.")
        except Exception as exc:
            self._record_error(exc)
            words = len(answer.split())
            if words < 20:
                return "**Score: 4/10**\n\nYour answer is a useful start, but it needs a concrete example. Add the situation, your action, and a measurable result.\n\n**Follow-up:** What changed because of your work?"
            return "**Score: 7/10**\n\nYou gave enough detail to start a strong answer. Make the result more measurable and connect the example directly to the internship requirement.\n\n**Follow-up:** What did you learn and what would you improve next time?"

    @staticmethod
    def _source_requirements(description: str) -> list[str]:
        """Extract compact requirement anchors without inventing role facts."""
        raw_lines = [re.sub(r"^[-*•\d.)\s]+", "", line).strip() for line in description.splitlines()]
        candidates = [line for line in raw_lines if len(line.split()) >= 2]
        if not candidates:
            sentences = re.split(r"[.!?;]+", description)
            candidates = [sentence.strip() for sentence in sentences if len(sentence.split()) >= 2]
        anchors: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            cleaned = re.sub(r"\s+", " ", candidate).strip(" .,:;-")
            key = cleaned.lower()
            if cleaned and key not in seen:
                anchors.append(cleaned[:180])
                seen.add(key)
        return anchors[:12]

    @staticmethod
    def _basis_is_in_source(basis: str, description: str) -> bool:
        source = re.sub(r"\s+", " ", description.lower()).strip()
        basis_text = re.sub(r"\s+", " ", basis.lower()).strip()
        if len(basis_text) >= 8 and basis_text in source:
            return True
        basis_terms = {term for term in re.findall(r"[a-z0-9+#.]{4,}", basis_text) if term not in {"role", "source", "requirement", "practice", "description"}}
        source_terms = set(re.findall(r"[a-z0-9+#.]{4,}", source))
        return bool(basis_terms) and len(basis_terms & source_terms) >= max(1, min(3, len(basis_terms) // 2))

    def generate_interview_bank(self, role: str, description: str, topics: list[str], candidate_context: str = "") -> dict[str, Any]:
        try:
            raw = self._generate(interview_question_prompt(role, description, topics, candidate_context), "You are an expert interview curriculum designer. The role description is the source of truth; reject generic content.")
            parsed = self._parse_json(raw)
            questions = parsed.get("questions", []) if isinstance(parsed, dict) else []
            grounded = [
                question for question in questions
                if isinstance(question, dict)
                and question.get("question")
                and question.get("requirement_basis")
                and self._basis_is_in_source(str(question["requirement_basis"]), description)
            ]
            minimum = max(3, min(10, len(questions)))
            if parsed and len(grounded) >= minimum:
                parsed["questions"] = grounded
                parsed["requirements_extracted"] = [str(item) for item in parsed.get("requirements_extracted", []) if self._basis_is_in_source(str(item), description)]
                parsed["skill_rubric"] = [str(item) for item in parsed.get("skill_rubric", []) if self._basis_is_in_source(str(item), description)]
                return parsed
        except Exception as exc:
            self._record_error(exc)
        return self.demo_interview_bank(role, topics, description)

    def interview_assistant(self, role: str, context: str, history: list[dict[str, str]], user_message: str) -> str:
        history_text = "\n".join(f"{item['speaker']}: {item['text']}" for item in history[-8:])
        try:
            return self._generate(interview_assistant_prompt(role, context, history_text, user_message), "You are a patient and rigorous interview assistant.")
        except Exception as exc:
            self._record_error(exc)
            return f"Provider unavailable. I did not receive a Grok response. For **{role}**, connect your answer to one exact requirement from the role description.\n\nLocal fallback: use **Situation → Task → Action → Result** and name the requirement you are proving."

    def evaluate_interview_answer(self, role: str, context: str, question: str, answer: str, rubric: list[str]) -> dict[str, Any]:
        try:
            raw = self._generate(answer_evaluation_prompt(role, context, question, answer, rubric), "You are a fair structured interview evaluator. Ground every judgment in the supplied role context.")
            parsed = self._parse_json(raw)
            if parsed and "score" in parsed:
                return parsed
        except Exception as exc:
            self._record_error(exc)
        score = min(10, 4 + (2 if len(answer.split()) >= 30 else 0) + (2 if any(token in answer.lower() for token in ["because", "result", "built", "reduced", "learned"]) else 0))
        return {"score": score, "requirement_addressed": "Demo mode could not call the provider; connect your answer to the requirement named in the question.", "skill_scores": {skill: score for skill in rubric[:5]}, "strengths": ["You attempted the question directly."], "improvements": ["Add a concrete example and measurable result.", "Connect the answer to the exact role requirement."], "model_answer_outline": ["State the situation and task.", "Explain your specific action.", "Close with the result and learning."], "follow_up": "Which exact responsibility from the role description does this example prove?"}

    def evaluate(self, scenario: dict, transcript: list[dict[str, str]]) -> dict[str, Any]:
        transcript_text = "\n".join(f"{item['speaker']}: {item['text']}" for item in transcript)
        try:
            raw = self._generate(evaluation_prompt(scenario, transcript_text), "You are a structured career coach.")
            parsed = self._parse_json(raw)
            if parsed and isinstance(parsed.get("scores"), dict):
                return parsed
        except Exception as exc:
            self._record_error(exc)
        return self.demo_evaluation(scenario, transcript)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any] | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

    @staticmethod
    def demo_role_match(resume_text: str, job_text: str) -> dict[str, Any]:
        resume_lower = resume_text.lower()
        keywords = ["python", "sql", "machine learning", "javascript", "react", "streamlit", "communication", "excel", "data analysis", "git"]
        matched = [word.title() for word in keywords if word in resume_lower]
        missing = [word.title() for word in keywords if word in job_text.lower() and word not in resume_lower]
        questions = [
            {"question": "Walk me through a project from your resume that is most relevant to this internship.", "why_it_matters": "Tests evidence and relevance.", "ideal_points": ["Context", "Your contribution", "Result"]},
            {"question": "Which requirement in this internship description would you need to learn fastest, and how would you approach it?", "why_it_matters": "Tests self-awareness and learning agility.", "ideal_points": ["Honest gap", "Specific learning plan", "Time frame"]},
            {"question": "Tell me about a time you solved a difficult technical or team problem.", "why_it_matters": "Tests problem-solving and collaboration.", "ideal_points": ["Situation", "Action", "Outcome"]},
            {"question": "Why are you interested in this internship and what would you contribute in the first 30 days?", "why_it_matters": "Tests motivation and preparation.", "ideal_points": ["Role connection", "Relevant strength", "Practical first step"]},
            {"question": "How do you respond when feedback shows that your first solution is not good enough?", "why_it_matters": "Tests coachability.", "ideal_points": ["Specific example", "Adaptation", "Improved result"]},
            {"question": "What questions would you ask the team before accepting this internship?", "why_it_matters": "Tests curiosity and judgment.", "ideal_points": ["Mentorship", "Success measures", "Team workflow"]},
        ]
        return {"match_score": min(95, 45 + len(matched) * 7 - len(missing) * 3), "role_summary": "A tailored internship practice plan based on the uploaded documents.", "matched_skills": matched or ["Transferable project experience"], "missing_skills": missing or ["Validate the role-specific tools from the description"], "evidence": ["Demo mode uses only the uploaded text and does not invent resume achievements."], "questions": questions, "study_plan": ["Prepare two STAR stories from your resume.", "Review the top missing skill and build a small example.", "Practise explaining one project in 60 seconds.", "Prepare three questions for the interviewer."]}

    @staticmethod
    def demo_interview_bank(role: str, topics: list[str], description: str = "") -> dict[str, Any]:
        selected = topics or ["Behavioral", "Technical", "Projects"]
        requirements = AIEngine._source_requirements(description)
        if not requirements:
            requirements = [f"The description for {role} was not specific enough to extract a requirement"]
        templates = [
            ("Technical", "How would you demonstrate or apply this requirement in a project?"),
            ("Projects", "Describe evidence from your work that would help you meet this requirement."),
            ("Role fit", "What would you clarify with the interviewer before claiming you can meet this requirement?"),
            ("Behavioral", "Tell me about a time you handled a situation related to this requirement."),
            ("Learning", "How would you learn this requirement if it is currently a gap?"),
            ("Communication", "Explain your approach to this requirement to a non-technical teammate."),
        ]
        questions: list[dict[str, Any]] = []
        for index, requirement in enumerate(requirements):
            topic, template = templates[index % len(templates)]
            if topic not in selected and selected:
                topic = selected[index % len(selected)]
            questions.append({
                "topic": topic,
                "difficulty": "Intermediate",
                "question": f"The internship description states: ‘{requirement}’. {template}",
                "requirement_basis": requirement,
                "ideal_points": ["Quote the requirement accurately", "Use evidence or state the gap honestly", "Explain the next action or measurable result"],
            })
        return {
            "role_summary": f"Local fallback for {role}: every question is built from the supplied description; no generic requirement was added.",
            "requirements_extracted": requirements,
            "questions": questions,
            "skill_rubric": requirements[:8],
            "coding_focus": [item for item in requirements if any(token in item.lower() for token in ["code", "python", "sql", "java", "javascript", "algorithm", "data structure"])][:5],
        }

    @staticmethod
    def demo_hr_response(scenario: dict, round_number: int) -> str:
        prompts = [
            f"Thanks for explaining your target. What specific skills or measurable outcomes make INR {scenario['target_amount']:,.0f} appropriate for this {scenario['role']} role?",
            "That is useful context. If the base amount cannot move immediately, which combination of learning opportunities, review timing, or benefits would you consider?",
            "We are close to our current band. Give me your strongest concise closing case, including the value you expect to create in your first 90 days.",
        ]
        return prompts[min(max(round_number // 2, 0), len(prompts) - 1)]

    @staticmethod
    def demo_evaluation(scenario: dict, transcript: list[dict[str, str]]) -> dict[str, Any]:
        user_text = " ".join(item["text"] for item in transcript if item["speaker"] == "Candidate").lower()
        evidence = 2 if any(word in user_text for word in ["built", "increased", "reduced", "project", "%", "users"]) else 0
        flexibility = 2 if any(word in user_text for word in ["benefit", "review", "learning", "flexible", "bonus"]) else 0
        confidence = 2 if len(user_text.split()) >= 35 else 0
        base = 5 + evidence + confidence
        scores = {dimension: 6.0 for dimension in DIMENSIONS}
        scores["Value justification"] = min(10, base)
        scores["Flexibility"] = min(10, 5 + flexibility)
        scores["Communication clarity"] = min(10, 5 + (1 if len(user_text.split()) >= 25 else 0))
        return {
            "scores": scores,
            "summary": "You maintained a professional practice conversation. The next improvement is to connect your target more clearly to measurable value and a flexible total-compensation plan.",
            "strengths": ["You engaged with the negotiation instead of avoiding the question.", "Your tone remained suitable for a workplace conversation.", "You created a clear starting point for discussing your expectations."],
            "weaknesses": ["Add measurable evidence from projects, internships, or coursework.", "Use a shorter structure: value, target, and flexibility.", "Prepare a specific response to a budget constraint."],
            "missed_opportunities": ["You could have quantified an outcome or responsibility.", "You could have introduced a review timeline or non-cash alternative."],
            "recommended_phrases": ["Based on the outcomes I delivered in..., I am targeting...", "I am open to discussing the total package, including...", "If the base cannot move today, could we agree on a review after..."],
            "seven_day_plan": ["Write three quantified achievements.", "Practise a 30-second value statement.", "Record one response and review your tone.", "Research the role requirements.", "Practise responding to a low offer.", "Prepare two non-cash alternatives.", "Run the simulation again and compare scores."],
        }
