from agent.graph import (
    choose_analysis_route,
    debugger_graph,
    run_debugger_graph,
)
from agent.state import AgentState


def create_authentication_state() -> AgentState:
    """Create a strong deterministic input."""

    return {
        "endpoint": "/api/login",
        "method": "POST",
        "status_code": 401,
        "error_message": "JWT token expired",
        "stack_trace": "",
    }


def create_unknown_state() -> AgentState:
    """Create an input without recognizable evidence."""

    return {
        "endpoint": "/api/test",
        "method": "POST",
        "status_code": None,
        "error_message": "Something unusual happened",
        "stack_trace": "",
    }


def test_langgraph_executes_rule_based_route_in_order() -> None:
    state = create_authentication_state()

    # Streaming updates reveals which graph nodes ran.
    updates = list(
        debugger_graph.stream(
            state,
            stream_mode="updates",
        )
    )

    executed_nodes = [next(iter(update)) for update in updates]

    assert executed_nodes == [
        "classify_failure",
        "generate_hypotheses",
        "match_evidence",
        "eliminate_hypotheses",
        "reason_root_cause",
        "mark_rule_based_route",
        "suggest_fixes",
    ]


def test_strong_result_uses_rule_based_route() -> None:
    result = run_debugger_graph(create_authentication_state())

    assert result["failure_type"] == "AUTHENTICATION"
    assert result["root_cause"] == "JWT token has expired"
    assert result["confidence_score"] >= 0.8

    assert result["analysis_route"] == "RULE_BASED"
    assert result["llm_used"] is False
    assert "meets" in result["routing_reason"]


def test_unknown_result_uses_llm_fallback_route() -> None:
    result = run_debugger_graph(create_unknown_state())

    assert result["failure_type"] == "UNKNOWN"
    assert result["analysis_route"] == "LLM_FALLBACK"
    assert result["llm_used"] is False
    assert "UNKNOWN" in result["routing_reason"]


def test_low_confidence_known_category_uses_fallback() -> None:
    state: AgentState = {
        "failure_type": "AUTHENTICATION",
        "confidence_score": 0.64,
    }

    assert choose_analysis_route(state) == "llm_fallback"


def test_threshold_score_uses_rule_based_route() -> None:
    state: AgentState = {
        "failure_type": "AUTHENTICATION",
        "confidence_score": 0.65,
    }

    assert choose_analysis_route(state) == "rule_based"


def test_langgraph_does_not_mutate_original_input() -> None:
    state = create_authentication_state()
    original_state = state.copy()

    run_debugger_graph(state)

    assert state == original_state
