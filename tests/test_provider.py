from modules.ai_engine import AIEngine


def test_demo_provider_is_available_without_credentials():
    engine = AIEngine("demo")
    assert engine.label == "Demo mode"
    assert not engine.available
    bank = engine.generate_interview_bank("Data Analyst Intern", "Python and SQL role", ["Technical"])
    assert bank["questions"]


def test_provider_labels_are_stable():
    assert AIEngine("gemini", "fake-key").label == "Gemini"
    assert AIEngine("grok", "fake-key").label == "Grok"
