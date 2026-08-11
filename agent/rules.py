from dataclasses import dataclass


AUTHENTICATION = "AUTHENTICATION"
AUTHORIZATION = "AUTHORIZATION"
VALIDATION = "VALIDATION"
SERVER_ERROR = "SERVER_ERROR"
DATABASE = "DATABASE"
DATABASE_CONCURRENCY = "DATABASE_CONCURRENCY"
UNKNOWN = "UNKNOWN"

KEYWORD_WEIGHT = 1
SERVER_ERROR_MIN_STATUS = 500
SERVER_ERROR_STATUS_WEIGHT = 5


@dataclass(frozen=True)
class StatusRule:
    """
    Classification rule associated with one exact HTTP status code.
    """

    category: str
    weight: int
    message: str


@dataclass(frozen=True)
class CategoryRule:
    """
    Text-based classification configuration for one category.
    """

    keywords: tuple[str, ...]
    strong_signals: tuple[str, ...] = ()
    strong_weight: int = 0


@dataclass(frozen=True)
class HypothesisTemplate:
    """
    Starting configuration for one possible root cause.
    """

    cause: str
    initial_score: float


STATUS_RULES: dict[int, StatusRule] = {
    400: StatusRule(
        category=VALIDATION,
        weight=5,
        message="HTTP 400 usually means invalid request data",
    ),
    401: StatusRule(
        category=AUTHENTICATION,
        weight=5,
        message="HTTP 401 usually means authentication failed",
    ),
    403: StatusRule(
        category=AUTHORIZATION,
        weight=5,
        message="HTTP 403 usually means access is forbidden",
    ),
}


CATEGORY_RULES: dict[str, CategoryRule] = {
    AUTHENTICATION: CategoryRule(
        keywords=(
            "jwt",
            "token expired",
            "unauthorized",
            "authentication failed",
        ),
    ),

    AUTHORIZATION: CategoryRule(
        keywords=(
            "forbidden",
            "permission denied",
            "insufficient permission",
            "insufficient scope",
            "access denied",
            "role required",
            "not allowed",
        ),
    ),

    VALIDATION: CategoryRule(
        keywords=(
            "required field",
            "is required",
            "missing field",
            "validation error",
        ),
    ),

    SERVER_ERROR: CategoryRule(
        keywords=(
            "traceback",
            "undefined",
            "nullpointer",
            "internal server error",
        ),
    ),

    DATABASE: CategoryRule(
        keywords=(
            "database",
            "postgres",
            "postgresql",
            "mysql",
            "sqlalchemy",
            "psycopg",
            "duplicate key",
            "unique constraint",
            "unique key",
            "sql syntax",
            "query failed",
            "integrityerror",
        ),
        strong_signals=(
            "database connection",
            "psycopg",
            "sqlalchemy.exc",
            "mysql.connector",
            "duplicate key",
            "unique constraint",
            "foreign key constraint",
            "sql syntax",
            "integrityerror",
        ),
        strong_weight=6,
    ),

    DATABASE_CONCURRENCY: CategoryRule(
        keywords=(
            "deadlock",
            "lock wait timeout",
            "lock timeout",
            "could not obtain lock",
            "database is locked",
            "could not serialize access",
            "serialization failure",
            "concurrent update",
            "optimistic lock",
            "stale object",
            "version conflict",
        ),
        strong_signals=(
            "deadlock detected",
            "deadlock found",
            "deadlock victim",
            "lock wait timeout",
            "could not obtain lock",
            "database is locked",
            "could not serialize access",
            "serialization failure",
            "concurrent update",
            "optimistic lock",
            "stale object",
            "version conflict",
        ),
        strong_weight=8,
    ),
}


HYPOTHESIS_TEMPLATES: dict[
    str,
    tuple[HypothesisTemplate, ...],
] = {
    AUTHENTICATION: (
        HypothesisTemplate(
            cause="JWT token has expired",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause=(
                "Authorization header is missing or malformed"
            ),
            initial_score=0.50,
        ),
        HypothesisTemplate(
            cause="Token signature verification failed",
            initial_score=0.40,
        ),
    ),

    AUTHORIZATION: (
        HypothesisTemplate(
            cause="User lacks required permission",
            initial_score=0.70,
        ),
        HypothesisTemplate(
            cause="Token has insufficient scope",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause=(
                "User role is not allowed for this resource"
            ),
            initial_score=0.50,
        ),
    ),

    VALIDATION: (
        HypothesisTemplate(
            cause="Required field is missing from request",
            initial_score=0.70,
        ),
        HypothesisTemplate(
            cause="Field type mismatch",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause="Field format validation failed",
            initial_score=0.50,
        ),
    ),

    SERVER_ERROR: (
        HypothesisTemplate(
            cause="Null pointer dereference",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause="Undefined variable or method call",
            initial_score=0.50,
        ),
        HypothesisTemplate(
            cause="Unhandled exception in application code",
            initial_score=0.40,
        ),
    ),

    DATABASE: (
        HypothesisTemplate(
            cause="Database connection is unavailable",
            initial_score=0.70,
        ),
        HypothesisTemplate(
            cause="Database constraint was violated",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause="Database query execution failed",
            initial_score=0.50,
        ),
    ),

    DATABASE_CONCURRENCY: (
        HypothesisTemplate(
            cause="Database deadlock occurred",
            initial_score=0.70,
        ),
        HypothesisTemplate(
            cause="Database lock wait timed out",
            initial_score=0.60,
        ),
        HypothesisTemplate(
            cause=(
                "Transaction serialization conflict occurred"
            ),
            initial_score=0.50,
        ),
    ),

    UNKNOWN: (
        HypothesisTemplate(
            cause=(
                "Insufficient information to identify "
                "the root cause"
            ),
            initial_score=0.20,
        ),
    ),
}