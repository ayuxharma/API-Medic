from typing import TypedDict


class HypothesisData(TypedDict):
    """
    Serializable representation of one hypothesis.
    """

    cause: str
    category: str
    score: float
    supporting_evidence: list[str]
    weakening_evidence: list[str]


class AlternativeCauseData(TypedDict):
    """
    Serializable representation of an alternative cause.
    """

    cause: str
    score: float
    relative_share: float


class AgentState(TypedDict, total=False):
    """
    Shared state passed through the debugging workflow.

    total=False means fields can be added gradually as the
    state moves through the pipeline.
    """

    # Input
    endpoint: str
    method: str
    status_code: int | None
    error_message: str
    stack_trace: str

    # Classification
    failure_type: str
    signals: list[str]

    # Hypothesis processing
    hypotheses: list[HypothesisData]

    # Final reasoning
    root_cause: str
    confidence_score: float
    alternative_causes: list[AlternativeCauseData]
    suggested_fixes: list[str]
