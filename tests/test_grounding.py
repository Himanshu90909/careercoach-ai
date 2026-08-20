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


def test_grok_uses_current_default_model():
    engine = AIEngine("grok", "test-key")
    assert engine.model == "grok-4.6"


def test_grok_error_does_not_expose_api_key():
    secret = "grok-test-secret"
    engine = AIEngine("grok", secret)
    engine._record_error(RuntimeError(f"401 invalid key {secret}"))
    assert secret not in engine.last_error
    assert "REDACTED" in engine.last_error


def test_demo_fallback_uses_only_supplied_requirements():
    description = "Build dashboards in SQL and explain findings to stakeholders."
    bank = AIEngine.demo_interview_bank("Product Analyst Intern", ["Technical", "Communication"], description)
    assert bank["requirements_extracted"] == [description.rstrip(".")]
    assert bank["questions"]
    normalized = description.rstrip(".")
    assert all(normalized in item["requirement_basis"] for item in bank["questions"])
    assert all(normalized in item["question"] for item in bank["questions"])


def test_unrelated_requirement_basis_is_not_grounded():
    description = "Build dashboards in SQL and explain findings to stakeholders."
    assert AIEngine._basis_is_in_source("Build dashboards in SQL", description)
    assert not AIEngine._basis_is_in_source("Kubernetes cluster administration", description)
