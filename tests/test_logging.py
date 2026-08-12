import logging

import pytest

from agent.state import AgentState
from agent.workflow import DebuggerWorkflow


def create_test_state() -> AgentState:
    """
    Create a valid diagnosis input containing sensitive text.
    """

    return {
        "endpoint": "/api/login",
        "method": "POST",
        "status_code": 401,
        "error_message": ("JWT token expired: secret-token-value"),
        "stack_trace": "",
    }


def test_workflow_logs_safe_summary(
    caplog,
) -> None:
    """
    Successful logs must contain metadata, not raw input.
    """

    caplog.set_level(
        logging.INFO,
        logger="agent.workflow",
    )

    workflow = DebuggerWorkflow()
    result = workflow.run(create_test_state())

    assert result["failure_type"] == ("AUTHENTICATION")

    assert "event=diagnosis_completed" in caplog.text
    assert "failure_type=AUTHENTICATION" in caplog.text
    assert "analysis_route=RULE_BASED" in caplog.text

    # Sensitive user input must never enter logs.
    assert "secret-token-value" not in caplog.text


def test_workflow_failure_logs_only_error_type(
    monkeypatch,
    caplog,
) -> None:
    """
    Failed diagnoses must not log sensitive exception text.
    """

    sensitive_message = "database password is private-password"

    def raise_unexpected_error(
        state: AgentState,
    ) -> AgentState:
        raise RuntimeError(sensitive_message)

    monkeypatch.setattr(
        "agent.workflow.run_debugger_graph",
        raise_unexpected_error,
    )

    caplog.set_level(
        logging.ERROR,
        logger="agent.workflow",
    )

    workflow = DebuggerWorkflow()

    with pytest.raises(RuntimeError):
        workflow.run(create_test_state())

    assert "event=diagnosis_failed" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert sensitive_message not in caplog.text
