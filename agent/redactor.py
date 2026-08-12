import re
from typing import TypedDict

from .state import AgentState


class SafeAnalysisContext(TypedDict):
    """
    Sanitized information allowed to be sent for external analysis.
    """

    endpoint: str
    method: str
    status_code: int | None
    error_message: str
    stack_trace: str
    failure_type: str
    signals: list[str]
    rule_based_root_cause: str
    rule_based_confidence: float


# Matches Authorization headers containing Bearer or Basic credentials.
_AUTHORIZATION_PATTERN = re.compile(
    r"(?P<prefix>\bauthorization\s*[:=]\s*)"
    r"(?:bearer|basic)\s+[^\s,;]+",
    re.IGNORECASE,
)

# Cookies can contain session identifiers and authentication data.
_COOKIE_PATTERN = re.compile(
    r"(?P<prefix>\b(?:set-cookie|cookie)\s*:\s*)[^\r\n]+",
    re.IGNORECASE,
)

# Matches credentials embedded inside common database URLs.
_DATABASE_URL_PATTERN = re.compile(
    r"(?P<scheme>"
    r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"
    r")"
    r"[^@\s/]+@",
    re.IGNORECASE,
)

# Matches a JWT consisting of header, payload, and signature sections.
_JWT_PATTERN = re.compile(
    r"\beyJ[A-Za-z0-9_-]{5,}"
    r"\.[A-Za-z0-9_-]{5,}"
    r"\.[A-Za-z0-9_-]{5,}\b"
)

# Matches provider-specific token formats.
_PROVIDER_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Common OpenAI API-key prefix.
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    # Common GitHub personal-access-token prefixes.
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    # Common AWS access-key prefixes.
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
)

# Matches values assigned to common secret-related field names.
_KEY_VALUE_PATTERN = re.compile(
    r"""
    (?P<prefix>
        ["']?
        (?:
            api[_-]?key
            | access[_-]?token
            | refresh[_-]?token
            | token
            | password
            | passwd
            | pwd
            | secret
            | client[_-]?secret
        )
        ["']?
        \s*[:=]\s*
    )
    (?:
        "(?P<double_value>[^"]*)"
        |
        '(?P<single_value>[^']*)'
        |
        (?P<bare_value>[^\s,;&]+)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _replace_secret_value(match: re.Match[str]) -> str:
    """
    Preserve the key and quote style while hiding its value.
    """

    prefix = match.group("prefix")

    if match.group("double_value") is not None:
        return f'{prefix}"[REDACTED]"'

    if match.group("single_value") is not None:
        return f"{prefix}'[REDACTED]'"

    return f"{prefix}[REDACTED]"


def redact_sensitive_text(text: str) -> str:
    """
    Replace common credentials with a safe placeholder.
    """

    if not text:
        return text

    redacted_text = text

    # Remove complete Authorization credentials.
    redacted_text = _AUTHORIZATION_PATTERN.sub(
        r"\g<prefix>[REDACTED]",
        redacted_text,
    )

    # Remove session and cookie values.
    redacted_text = _COOKIE_PATTERN.sub(
        r"\g<prefix>[REDACTED]",
        redacted_text,
    )

    # Preserve the database type but remove embedded credentials.
    redacted_text = _DATABASE_URL_PATTERN.sub(
        r"\g<scheme>[REDACTED]@",
        redacted_text,
    )

    # Remove standalone JSON Web Tokens.
    redacted_text = _JWT_PATTERN.sub(
        "[REDACTED]",
        redacted_text,
    )

    # Remove provider-specific token formats.
    for token_pattern in _PROVIDER_TOKEN_PATTERNS:
        redacted_text = token_pattern.sub(
            "[REDACTED]",
            redacted_text,
        )

    # Remove secrets written as key=value or key: value.
    redacted_text = _KEY_VALUE_PATTERN.sub(
        _replace_secret_value,
        redacted_text,
    )

    return redacted_text


def build_safe_analysis_context(
    state: AgentState,
) -> SafeAnalysisContext:
    """
    Create the only state subset that may be sent to an LLM.
    """

    return {
        # Endpoint query parameters may contain tokens.
        "endpoint": redact_sensitive_text(state.get("endpoint", "Not provided")),
        "method": state.get("method", "GET"),
        "status_code": state.get("status_code"),
        "error_message": redact_sensitive_text(state.get("error_message", "")),
        "stack_trace": redact_sensitive_text(state.get("stack_trace", "")),
        "failure_type": state.get("failure_type", "UNKNOWN"),
        "signals": [
            redact_sensitive_text(signal) for signal in state.get("signals", [])
        ],
        "rule_based_root_cause": redact_sensitive_text(
            state.get(
                "root_cause",
                "Unable to determine the root cause",
            )
        ),
        "rule_based_confidence": state.get(
            "confidence_score",
            0.0,
        ),
    }
