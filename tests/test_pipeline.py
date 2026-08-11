from agent.state import AgentState
from agent.workflow import DebuggerWorkflow


def run_pipeline(state: AgentState) -> AgentState:
    workflow = DebuggerWorkflow()
    return workflow.run(state)


def create_state(status_code, error_message, stack_trace="") -> AgentState:
    return {
        "endpoint": "/api/test",
        "method": "POST",
        "status_code": status_code,
        "error_message": error_message,
        "stack_trace": stack_trace,
    }


def test_expired_jwt_pipeline():
    state = create_state(401, "JWT token expired")
    result = run_pipeline(state)

    assert result["failure_type"] == "AUTHENTICATION"
    assert result["root_cause"] == "JWT token has expired"
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0

    primary = result["hypotheses"][0]

    assert primary["cause"] == "JWT token has expired"
    assert len(primary["supporting_evidence"]) > 0


def test_missing_field_pipeline():
    state = create_state(
        400,
        "Required field is missing",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "VALIDATION"
    assert result["root_cause"] == ("Required field is missing from request")
    assert len(result["suggested_fixes"]) > 0


def test_undefined_variable_pipeline():
    state = create_state(
        500,
        "Undefined variable user_id",
        "user_id is not defined",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "SERVER_ERROR"
    assert result["root_cause"] == ("Undefined variable or method call")


def test_permission_denied_pipeline() -> None:
    state = create_state(
        403,
        "Permission denied for this resource",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "AUTHORIZATION"
    assert result["root_cause"] == ("User lacks required permission")
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0

    primary = result["hypotheses"][0]

    assert primary["cause"] == ("User lacks required permission")
    assert len(primary["supporting_evidence"]) > 0


def test_unknown_error_pipeline():
    state = create_state(
        None,
        "Something unusual happened",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "UNKNOWN"
    assert result["root_cause"] == (
        "Insufficient information to identify the root cause"
    )
    assert len(result["suggested_fixes"]) > 0


def test_unrelated_evidence_does_not_reduce_authentication_score() -> None:
    state = create_state(
        401,
        "JWT token expired; permission denied",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "AUTHENTICATION"
    assert result["root_cause"] == "JWT token has expired"
    assert result["confidence_score"] >= 0.8

    primary = result["hypotheses"][0]

    assert all(
        "User lacks required permission" not in evidence
        for evidence in primary["weakening_evidence"]
    )


def test_database_connection_failure_pipeline() -> None:
    state = create_state(
        500,
        "Database connection refused",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE"
    assert result["root_cause"] == ("Database connection is unavailable")
    assert result["confidence_score"] >= 0.9
    assert len(result["suggested_fixes"]) > 0

    primary = result["hypotheses"][0]

    assert primary["cause"] == ("Database connection is unavailable")
    assert len(primary["supporting_evidence"]) > 0


def test_database_constraint_failure_pipeline() -> None:
    state = create_state(
        409,
        "Duplicate key violates unique constraint users_email_key",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE"
    assert result["root_cause"] == ("Database constraint was violated")
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0


def test_database_query_failure_pipeline() -> None:
    state = create_state(
        500,
        "SQL syntax error at or near FROM",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE"
    assert result["root_cause"] == ("Database query execution failed")
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0


def test_database_deadlock_pipeline() -> None:
    state = create_state(
        500,
        "Deadlock detected while waiting for transaction",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE_CONCURRENCY"

    assert result["root_cause"] == ("Database deadlock occurred")

    assert result["confidence_score"] >= 0.9
    assert len(result["suggested_fixes"]) > 0


def test_database_lock_timeout_pipeline() -> None:
    state = create_state(
        503,
        "Lock wait timeout exceeded",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE_CONCURRENCY"

    assert result["root_cause"] == ("Database lock wait timed out")

    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0


def test_transaction_serialization_conflict_pipeline() -> None:
    state = create_state(
        409,
        "Could not serialize access due to concurrent update",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "DATABASE_CONCURRENCY"

    assert result["root_cause"] == ("Transaction serialization conflict occurred")

    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0
