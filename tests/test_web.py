import logging

from fastapi.testclient import TestClient

from web.main import app

client = TestClient(app)


def test_home_route_displays_form() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "API Failure Debugger" in response.text
    assert 'action="/diagnose"' in response.text
    assert 'name="error_message"' in response.text


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_diagnose_expired_jwt() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "endpoint": "/api/login",
            "method": "post",
            "status_code": 401,
            "error_message": "JWT token expired",
            "stack_trace": "",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["endpoint"] == "/api/login"
    assert result["method"] == "POST"
    assert result["failure_type"] == "AUTHENTICATION"
    assert result["root_cause"] == "JWT token has expired"
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0


def test_diagnose_rejects_invalid_status_code() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "status_code": 99,
            "error_message": "Some error happened",
        },
    )

    assert response.status_code == 422


def test_diagnose_rejects_empty_error_message() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "status_code": 500,
            "error_message": "   ",
        },
    )

    assert response.status_code == 422


def test_html_form_runs_diagnosis() -> None:
    response = client.post(
        "/diagnose",
        data={
            "endpoint": "/api/login",
            "method": "POST",
            "status_code": "401",
            "error_message": "JWT token expired",
            "stack_trace": "",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "API Diagnosis Result" in response.text
    assert "AUTHENTICATION" in response.text
    assert "JWT token has expired" in response.text
    assert "Suggested fixes" in response.text


def test_upload_valid_error_file() -> None:
    file_content = """Endpoint: /api/login
Method: POST
Status Code: 401
Error Message:
JWT token expired
Stack Trace:
"""

    response = client.post(
        "/diagnose/upload",
        files={
            "file": (
                "auth-error.txt",
                file_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert "API Diagnosis Result" in response.text
    assert "AUTHENTICATION" in response.text
    assert "JWT token has expired" in response.text


def test_upload_rejects_missing_error_message() -> None:
    file_content = """Endpoint: /api/login
Method: POST
Status Code: 401
Error Message:
Stack Trace:
"""

    response = client.post(
        "/diagnose/upload",
        files={
            "file": (
                "invalid-error.txt",
                file_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Input error" in response.text
    assert "Error Message is required" in response.text


def test_upload_rejects_large_file() -> None:
    large_content = "x" * 100_001

    response = client.post(
        "/diagnose/upload",
        files={
            "file": (
                "large-error.txt",
                large_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert "100 KB or smaller" in response.text


def test_api_diagnoses_authorization_failure() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "endpoint": "/api/admin/users",
            "method": "DELETE",
            "status_code": 403,
            "error_message": ("Permission denied for this resource"),
            "stack_trace": "",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["failure_type"] == "AUTHORIZATION"
    assert result["root_cause"] == ("User lacks required permission")
    assert len(result["suggested_fixes"]) > 0


def test_api_diagnoses_database_failure() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "endpoint": "/api/users",
            "method": "POST",
            "status_code": 500,
            "error_message": "Database connection refused",
            "stack_trace": "",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["failure_type"] == "DATABASE"
    assert result["root_cause"] == ("Database connection is unavailable")
    assert len(result["suggested_fixes"]) > 0


def test_api_diagnoses_database_deadlock() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "endpoint": "/api/orders",
            "method": "POST",
            "status_code": 500,
            "error_message": ("Deadlock detected while waiting for transaction"),
            "stack_trace": "",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["failure_type"] == "DATABASE_CONCURRENCY"

    assert result["root_cause"] == ("Database deadlock occurred")

    assert len(result["suggested_fixes"]) > 0


def test_unexpected_api_error_returns_safe_response(
    monkeypatch,
    caplog,
) -> None:
    """
    Internal exceptions must not be exposed to clients.
    """

    sensitive_message = "database password is private-password"

    caplog.set_level(
        logging.ERROR,
        logger="web.main",
    )

    def raise_unexpected_error(payload):
        raise RuntimeError(sensitive_message)

    monkeypatch.setattr(
        "web.main.run_diagnosis",
        raise_unexpected_error,
    )

    response = client.post(
        "/api/diagnose",
        json={
            "status_code": 500,
            "error_message": "Unexpected failure",
        },
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": ("An unexpected internal error occurred."),
    }

    # Neither the HTTP response nor logs expose the secret.
    assert sensitive_message not in response.text
    assert sensitive_message not in caplog.text

    assert "error_type=RuntimeError" in caplog.text


def test_stylesheet_is_served() -> None:
    """
    The browser must be able to load the shared stylesheet.
    """

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "--background:" in response.text
