from fastapi.testclient import TestClient

from web.main import app


client = TestClient(app)


def test_home_route() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "API Failure Debugger is running",
        "documentation": "/docs",
        "health_check": "/health",
    }


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