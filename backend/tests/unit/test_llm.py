"""Unit tests for the LLM adapter layer."""

from stadiummind.core.config import Settings
from stadiummind.llm.adapter import MockLLM, build_llm


def test_mock_llm_is_deterministic():
    llm = MockLLM()
    a = llm.complete("Context: Gate 3 is full.\n\nQuestion: what to do?")
    b = llm.complete("Context: Gate 3 is full.\n\nQuestion: what to do?")
    assert a == b
    assert "Gate 3" in a


def test_explain_wraps_context():
    llm = MockLLM()
    out = llm.explain("Gate 5 is 20% full.", "Redirect fans?")
    assert isinstance(out, str) and len(out) > 0


def test_build_llm_defaults_to_mock_without_key():
    s = Settings(gemini_api_key=None)
    assert build_llm(s).name == "mock"


def test_force_mock_overrides_key():
    s = Settings(gemini_api_key="fake", force_mock_llm=True)
    assert s.gemini_enabled is False
    assert build_llm(s).name == "mock"
