from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DiagnosisRequest(BaseModel):
    """
    Input received when a client requests an API diagnosis.
    """

    endpoint: str = Field(
        default="Not provided",
        max_length=2048,
    )

    method: str = Field(
        default="GET",
        min_length=1,
        max_length=20,
    )

    status_code: int | None = Field(
        default=None,
        ge=100,
        le=599,
    )

    error_message: str = Field(
        min_length=1,
        max_length=10_000,
    )

    stack_trace: str = Field(
        default="",
        max_length=50_000,
    )

    @field_validator("endpoint")
    @classmethod
    def normalize_endpoint(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            return "Not provided"

        return cleaned_value

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        cleaned_value = value.strip().upper()

        if not cleaned_value:
            raise ValueError("HTTP method cannot be empty")

        return cleaned_value

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Error message cannot be empty")

        return cleaned_value


class HypothesisResponse(BaseModel):
    """
    One possible explanation for the API failure.
    """

    cause: str
    category: str
    score: float
    supporting_evidence: list[str]
    weakening_evidence: list[str]


class AlternativeCauseResponse(BaseModel):
    """
    A lower-ranked possible cause.
    """

    cause: str
    score: float
    relative_share: float


class DiagnosisResponse(BaseModel):
    """
    Complete result returned by the debugging workflow.
    """

    endpoint: str
    method: str
    status_code: int | None
    error_message: str
    stack_trace: str

    failure_type: str
    signals: list[str]
    hypotheses: list[HypothesisResponse]

    root_cause: str
    confidence_score: float
    alternative_causes: list[AlternativeCauseResponse]

    # Explain which workflow branch produced the result.
    analysis_route: Literal[
        "RULE_BASED",
        "LLM_FALLBACK",
    ]
    routing_reason: str
    llm_used: bool
    llm_explanation: str
    llm_status_message: str

    suggested_fixes: list[str]
