import pytest
from pydantic import ValidationError

from agent.llm_analyzer import (
    LLMAnalysis,
    LLMAnalyzer,
)


def test_llm_analysis_accepts_valid_result() -> None:
    analysis = LLMAnalysis(
        root_cause="Upstream service was unavailable",
        explanation=("The response indicates an upstream failure."),
        confidence_score=0.75,
        suggested_fixes=[
            "Check upstream service health",
            "Add timeout handling",
        ],
    )

    assert analysis.confidence_score == 0.75
    assert len(analysis.suggested_fixes) == 2


def test_llm_analysis_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        LLMAnalysis(
            root_cause="Example failure",
            explanation="Example explanation",
            confidence_score=1.5,
            suggested_fixes=["Inspect the logs"],
        )


def test_llm_analysis_rejects_blank_root_cause() -> None:
    with pytest.raises(ValidationError):
        LLMAnalysis(
            root_cause="   ",
            explanation="Example explanation",
            confidence_score=0.5,
            suggested_fixes=["Inspect the logs"],
        )


def test_llm_analysis_rejects_empty_fixes() -> None:
    with pytest.raises(ValidationError):
        LLMAnalysis(
            root_cause="Example failure",
            explanation="Example explanation",
            confidence_score=0.5,
            suggested_fixes=[],
        )


def test_analyzer_is_unavailable_when_disabled(
    monkeypatch,
) -> None:
    """
    A configured key must not override the feature flag.
    """

    monkeypatch.setenv(
        "ENABLE_LLM_FALLBACK",
        "false",
    )
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    analyzer = LLMAnalyzer()

    assert analyzer.is_available() is False


def test_analyzer_is_unavailable_without_key(
    monkeypatch,
) -> None:
    """
    Enabled fallback still requires a Gemini key.
    """

    monkeypatch.setenv(
        "ENABLE_LLM_FALLBACK",
        "true",
    )
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    analyzer = LLMAnalyzer()

    assert analyzer.is_available() is False


def test_analyzer_is_available_with_gemini_key(
    monkeypatch,
) -> None:
    """
    Enabled fallback and a Gemini key allow analysis.
    """

    monkeypatch.setenv(
        "ENABLE_LLM_FALLBACK",
        "true",
    )
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-key",
    )

    analyzer = LLMAnalyzer()

    assert analyzer.is_available() is True
