from agent.classifier import FailureClassifier
from agent.state import AgentState


def create_state(status_code, error_message, stack_trace="") -> AgentState:
    return {
        "endpoint": "/api/test",
        "method": "GET",
        "status_code": status_code,
        "error_message": error_message,
        "stack_trace": stack_trace,
    }


def test_authentication_classification():
    state = create_state(401, "JWT token expired")

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "AUTHENTICATION"
    assert len(result["signals"]) > 0


def test_validation_classification():
    state = create_state(
        400,
        "Required field email is missing",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "VALIDATION"


def test_server_error_classification():
    state = create_state(
        500,
        "Undefined variable user_id",
        "Traceback: user_id is not defined",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "SERVER_ERROR"


def test_authorization_classification() -> None:
    state = create_state(
        403,
        "Permission denied for this resource",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "AUTHORIZATION"
    assert any("HTTP 403" in signal for signal in result["signals"])


def test_unknown_classification():
    state = create_state(
        None,
        "Something unexpected happened",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "UNKNOWN"


def test_database_classification() -> None:
    state = create_state(
        500,
        "Database connection refused",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "DATABASE"

    assert any(
        "strong database signal" in signal.lower() for signal in result["signals"]
    )


def test_database_concurrency_classification() -> None:
    state = create_state(
        500,
        "Deadlock detected while waiting for transaction",
    )

    result = FailureClassifier().classify(state)

    assert result["failure_type"] == "DATABASE_CONCURRENCY"

    assert any(
        "database-concurrency signal" in signal.lower() for signal in result["signals"]
    )
