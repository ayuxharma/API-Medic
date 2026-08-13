import pytest


@pytest.fixture(autouse=True)
def disable_live_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Prevent tests from making real external LLM requests.
    """

    monkeypatch.setenv(
        "ENABLE_LLM_FALLBACK",
        "false",
    )
