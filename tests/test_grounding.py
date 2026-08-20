from modules.ai_engine import AIEngine
from modules.prompts import interview_question_prompt


def test_question_prompt_contains_source_description_and_grounding_rules():
    prompt = interview_question_prompt(
        "Product Analyst Intern",
        "Build dashboards in SQL and explain findings to stakeholders.",
        ["Technical", "Communication"],
        "Built a small analytics dashboard.",
    )
    assert "Build dashboards in SQL" in prompt
    assert "single source of truth" in prompt
    assert "requirement_basis" in prompt


def test_grok_error_does_not_expose_api_key():
    secret = "grok-test-secret"
    engine = AIEngine("grok", secret)
    engine._record_error(RuntimeError(f"401 invalid key {secret}"))
    assert secret not in engine.last_error
    assert "REDACTED" in engine.last_error
