import pytest
from pydantic import ValidationError

from agent.llm_analyzer import LLMAnalysis


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
