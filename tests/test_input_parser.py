import pytest

from agent.input_parser import FileInputParser


def test_parse_valid_error_file(tmp_path):
    error_file = tmp_path / "auth_error.txt"

    error_file.write_text(
        """
Endpoint: /api/login
Method: POST
Status Code: 401
Error Message:
JWT token expired
Stack Trace:
AuthenticationError: token expired
""".strip(),
        encoding="utf-8",
    )

    state = FileInputParser().parse(str(error_file))

    assert state["endpoint"] == "/api/login"
    assert state["method"] == "POST"
    assert state["status_code"] == 401
    assert state["error_message"] == "JWT token expired"

    assert "AuthenticationError" in state["stack_trace"]


def test_parse_inline_error_message(tmp_path):
    error_file = tmp_path / "inline_error.txt"

    error_file.write_text(
        """
Endpoint: /api/login
Method: POST
Status Code: 401
Error Message: JWT token expired
Stack Trace:
""".strip(),
        encoding="utf-8",
    )

    state = FileInputParser().parse(str(error_file))

    assert state["error_message"] == "JWT token expired"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        FileInputParser().parse("samples/file-does-not-exist.txt")


def test_invalid_status_code(tmp_path):
    error_file = tmp_path / "invalid_status.txt"

    error_file.write_text(
        """
Endpoint: /api/login
Method: POST
Status Code: unauthorized
Error Message:
JWT token expired
Stack Trace:
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid status code",
    ):
        FileInputParser().parse(str(error_file))


def test_missing_error_message(tmp_path):
    error_file = tmp_path / "missing_error.txt"

    error_file.write_text(
        """
Endpoint: /api/login
Method: POST
Status Code: 401
Stack Trace:
AuthenticationError
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Error Message",
    ):
        FileInputParser().parse(str(error_file))
