from agent.redactor import (
    build_safe_analysis_context,
    redact_sensitive_text,
)
from agent.state import AgentState


def test_redacts_authorization_header() -> None:
    text = "Authorization: Bearer abc123.secret456.signature789"

    result = redact_sensitive_text(text)

    assert result == "Authorization: [REDACTED]"


def test_redacts_password_assignment() -> None:
    text = 'Database failed with password="super secret password"'

    result = redact_sensitive_text(text)

    assert "super secret password" not in result
    assert 'password="[REDACTED]"' in result


def test_redacts_api_key_assignment() -> None:
    text = "api_key=private-api-key-value"

    result = redact_sensitive_text(text)

    assert result == "api_key=[REDACTED]"


def test_redacts_database_url_credentials() -> None:
    text = "Connection failed: postgresql://admin:database-password@localhost/app"

    result = redact_sensitive_text(text)

    assert "admin" not in result
    assert "database-password" not in result
    assert "postgresql://[REDACTED]@localhost/app" in result


def test_redacts_cookie_header() -> None:
    text = "Cookie: session_id=private-session-value"

    result = redact_sensitive_text(text)

    assert result == "Cookie: [REDACTED]"


def test_preserves_normal_debugging_information() -> None:
    text = "JWT token expired while calling /api/login"

    result = redact_sensitive_text(text)

    # Ordinary diagnostic wording must remain useful.
    assert result == text


def test_safe_context_redacts_secrets() -> None:
    state: AgentState = {
        "endpoint": "/api/users?token=private-token",
        "method": "GET",
        "status_code": 500,
        "error_message": "Database connection failed",
        "stack_trace": 'password="database-password"',
        "failure_type": "DATABASE",
        "signals": ["Database connection wording found"],
        "root_cause": "Database connection is unavailable",
        "confidence_score": 0.4,
    }

    safe_context = build_safe_analysis_context(state)

    assert "private-token" not in safe_context["endpoint"]
    assert "database-password" not in safe_context["stack_trace"]
    assert "[REDACTED]" in safe_context["endpoint"]
    assert "[REDACTED]" in safe_context["stack_trace"]


def test_safe_context_does_not_modify_original_state() -> None:
    state: AgentState = {
        "endpoint": "/api/login",
        "method": "POST",
        "status_code": 401,
        "error_message": "api_key=private-value",
        "stack_trace": "",
    }

    original_state = state.copy()

    build_safe_analysis_context(state)

    # Sanitization must not destroy the caller's original data.
    assert state == original_state
