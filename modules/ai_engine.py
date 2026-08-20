"""Gemini integration with deterministic demo fallbacks."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from .prompts import evaluation_prompt, hr_system_prompt
from .scoring import DIMENSIONS

try:
    from google import genai
except ImportError:  # pragma: no cover - handled by requirements.txt
    genai = None


class AIEngine:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = genai.Client(api_key=self.api_key) if genai and self.api_key else None

    @property
    def available(self) -> bool:
        return self.client is not None

    def _generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"system_instruction": system_instruction, "temperature": 0.7},
        )
        return (response.text or "").strip()

    def hr_response(self, scenario: dict, transcript: list[dict[str, str]]) -> str:
        context = "\n".join(f"{item['speaker']}: {item['text']}" for item in transcript[-8:])
        prompt = f"Conversation so far:\n{context}\n\nRespond as the HR manager for the next round."
        try:
            return self._generate(prompt, hr_system_prompt(scenario))
        except Exception:
            return self.demo_hr_response(scenario, len(transcript))

    def evaluate(self, scenario: dict, transcript: list[dict[str, str]]) -> dict[str, Any]:
        transcript_text = "\n".join(f"{item['speaker']}: {item['text']}" for item in transcript)
        try:
            raw = self._generate(evaluation_prompt(scenario, transcript_text), "You are a structured career coach.")
            parsed = self._parse_json(raw)
            if parsed and isinstance(parsed.get("scores"), dict):
                return parsed
        except Exception:
            pass
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
