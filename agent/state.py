from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # input data
    status_code: str | None
    error_message: str
    stack_trace: str
    endpoint: str
    method: str

    # classsification results
    failure_type: str | None
    signals: list[str]

    # Hyothesis result
    hypotheses: list[dict[str, Any]]

    # final reasoning result
    root_cause: str
    confidence_score: float
    alternative_causes: list[dict[str, Any]]

    suggested_fixes: list[str]
