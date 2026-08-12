from typing import Literal, TypedDict

# These are the only valid routes through the workflow.
AnalysisRoute = Literal[
    "RULE_BASED",
    "LLM_FALLBACK",
]


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
    Serializable representation of one alternative cause.
    """

    cause: str
    score: float
    relative_share: float


class AgentState(TypedDict, total=False):
    """
    Shared state passed through the debugging workflow.

    total=False allows fields to be added gradually as the
    state moves through the graph.
    """

    # Original user input
    endpoint: str
    method: str
    status_code: int | None
    error_message: str
    stack_trace: str

    # Classification result
    failure_type: str
    signals: list[str]

    # Hypothesis processing
    hypotheses: list[HypothesisData]

    # Root-cause reasoning
    root_cause: str
    confidence_score: float
    alternative_causes: list[AlternativeCauseData]

    # Workflow routing
    analysis_route: AnalysisRoute
    routing_reason: str
    llm_used: bool
    llm_explanation: str
    llm_status_message: str

    # Final output
    suggested_fixes: list[str]
