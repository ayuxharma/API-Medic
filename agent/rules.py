from dataclasses import dataclass

AUTHENTICATION = "AUTHENTICATION"
AUTHORIZATION = "AUTHORIZATION"
VALIDATION = "VALIDATION"
SERVER_ERROR = "SERVER_ERROR"
DATABASE = "DATABASE"
DATABASE_CONCURRENCY = "DATABASE_CONCURRENCY"
UNKNOWN = "UNKNOWN"

KEYWORD_WEIGHT = 1
COMPETING_EVIDENCE_PENALTY = 0.15
SERVER_ERROR_MIN_STATUS = 500
SERVER_ERROR_STATUS_WEIGHT = 5


@dataclass(frozen=True)
class StatusRule:
    """Classification rule for one exact HTTP status code."""

    category: str
    weight: int
    message: str


@dataclass(frozen=True)
class CategoryRule:
    """Text-based classification configuration for one category."""

    keywords: tuple[str, ...]
    strong_signals: tuple[str, ...] = ()
    strong_weight: int = 0


@dataclass(frozen=True)
class HypothesisTemplate:
    """Starting configuration for one possible root cause."""

    cause: str
    initial_score: float


@dataclass(frozen=True)
class HypothesisEvaluationRule:
    """Evidence, elimination, and fix configuration for one cause."""

    pattern: str
    supporting_message: str
    weakening_message: str
    fixes: tuple[str, ...]
    support_weight: float = 0.30
    absence_penalty: float = 0.10


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
            cause="Authorization header is missing or malformed",
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
            cause="User role is not allowed for this resource",
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
            cause="Transaction serialization conflict occurred",
            initial_score=0.50,
        ),
    ),
    UNKNOWN: (
        HypothesisTemplate(
            cause="Insufficient information to identify the root cause",
            initial_score=0.20,
        ),
    ),
}


HYPOTHESIS_EVALUATION_RULES: dict[
    str,
    HypothesisEvaluationRule,
] = {
    "JWT token has expired": HypothesisEvaluationRule(
        pattern=r"(jwt|token).*(expired|expiration)",
        supporting_message="Token-expiration wording was found",
        weakening_message="No token-expiration wording was found",
        fixes=(
            "Generate a new authentication token.",
            "Check the JWT exp claim to confirm its expiry time.",
            "Ensure the client refreshes expired tokens before retrying.",
        ),
    ),
    "Authorization header is missing or malformed": HypothesisEvaluationRule(
        pattern=(
            r"(authorization|auth).*(missing|absent|required)"
            r"|missing.*(authorization|auth)"
        ),
        supporting_message="Authorization-header absence was found",
        weakening_message=("No missing Authorization-header wording was found"),
        fixes=(
            "Send an Authorization header with the request.",
            "Use the format: Bearer <token>.",
            "Check whether a proxy or frontend is removing the header.",
        ),
    ),
    "Token signature verification failed": HypothesisEvaluationRule(
        pattern=(
            r"signature.*(invalid|failed|verification)"
            r"|invalid.*signature"
        ),
        supporting_message="Token-signature failure wording was found",
        weakening_message="No token-signature failure wording was found",
        fixes=(
            "Check that signing and verification use the same key.",
            "Confirm the JWT algorithm matches the expected algorithm.",
            "Verify that the token was not changed or corrupted.",
        ),
    ),
    "User lacks required permission": HypothesisEvaluationRule(
        pattern=(
            r"permission.*(denied|missing|required|insufficient)"
            r"|(?:denied|missing|insufficient).*permission"
            r"|access denied"
        ),
        supporting_message="Permission-denial wording was found",
        weakening_message="No permission-denial wording was found",
        fixes=(
            "Check which permission the endpoint requires.",
            "Grant the permission only if the user should have access.",
            "Verify that the permission check uses the correct user.",
        ),
    ),
    "Token has insufficient scope": HypothesisEvaluationRule(
        pattern=(
            r"insufficient.*scope"
            r"|scope.*(missing|required|insufficient)"
        ),
        supporting_message="Insufficient token-scope wording was found",
        weakening_message="No insufficient-scope wording was found",
        fixes=(
            "Inspect the scopes included in the access token.",
            "Request a token containing the required scope.",
            "Verify that the API checks the intended scope name.",
        ),
    ),
    "User role is not allowed for this resource": HypothesisEvaluationRule(
        pattern=(
            r"role.*(required|forbidden|denied|not allowed)"
            r"|(?:required|forbidden).*role"
        ),
        supporting_message="Role-based access wording was found",
        weakening_message="No role-based access wording was found",
        fixes=(
            "Check which roles can access the resource.",
            "Verify that the user has the correct role.",
            "Review the role-based policy for the endpoint.",
        ),
    ),
    "Required field is missing from request": HypothesisEvaluationRule(
        pattern=r"(required|missing).*(field|parameter|email)",
        supporting_message="Required or missing request field was found",
        weakening_message="No required or missing field wording was found",
        fixes=(
            "Add the required field to the request body.",
            "Compare the request with the API schema.",
            "Check spelling and capitalization of field names.",
        ),
    ),
    "Field type mismatch": HypothesisEvaluationRule(
        pattern=r"type mismatch|expected.*got|invalid type",
        supporting_message="Field type-mismatch wording was found",
        weakening_message="No field type-mismatch wording was found",
        fixes=(
            "Check the expected data type in the API schema.",
            "Convert the submitted value to the required type.",
            "Check numbers, booleans, strings, arrays, and objects.",
        ),
    ),
    "Field format validation failed": HypothesisEvaluationRule(
        pattern=(
            r"invalid.*(email|url|date|format)"
            r"|format validation"
        ),
        supporting_message="Invalid field-format wording was found",
        weakening_message="No invalid field-format wording was found",
        fixes=(
            "Check the required format for the field.",
            "Validate email, URL, date, or UUID values.",
            "Compare the submitted value with the API schema.",
        ),
    ),
    "Null pointer dereference": HypothesisEvaluationRule(
        pattern=r"nullpointer|null pointer|nonetype",
        supporting_message="Null-reference wording was found",
        weakening_message="No null-reference wording was found",
        fixes=(
            "Find the variable that is null before it is used.",
            "Add a null check or initialize the missing value.",
            "Use the stack trace to locate the failing line.",
        ),
    ),
    "Undefined variable or method call": HypothesisEvaluationRule(
        pattern=r"undefined|not defined",
        supporting_message="Undefined-reference wording was found",
        weakening_message="No undefined-reference wording was found",
        fixes=(
            "Check the spelling of the variable or method.",
            "Create the variable before it is used.",
            "Inspect imports and object properties.",
        ),
    ),
    "Unhandled exception in application code": HypothesisEvaluationRule(
        pattern=r"traceback|unhandled exception|exception",
        supporting_message="Unhandled-exception wording was found",
        weakening_message="No unhandled-exception wording was found",
        fixes=(
            "Inspect the stack trace to locate the failing line.",
            "Handle the expected exception near the operation.",
            "Add validation and logging around the failure.",
        ),
        support_weight=0.20,
    ),
    "Database connection is unavailable": HypothesisEvaluationRule(
        pattern=(
            r"database.*connection.*(refused|failed|timeout|unavailable)"
            r"|(?:could not|cannot|failed to).*connect.*"
            r"(database|postgres|postgresql|mysql)"
            r"|too many connections"
        ),
        supporting_message="Database-connection failure wording was found",
        weakening_message=("No database-connection failure wording was found"),
        fixes=(
            "Verify that the database is running and reachable.",
            "Check the hostname, port, username, and connection URL.",
            "Inspect firewall and connection-pool limits.",
        ),
    ),
    "Database constraint was violated": HypothesisEvaluationRule(
        pattern=(
            r"duplicate key"
            r"|unique constraint"
            r"|unique violation"
            r"|foreign key constraint"
            r"|integrityerror"
            r"|not-null constraint"
        ),
        supporting_message="Database-constraint violation wording was found",
        weakening_message=("No database-constraint violation wording was found"),
        fixes=(
            "Inspect the database constraint in the error.",
            "Check for duplicate or missing related data.",
            "Validate unique, foreign-key, and required values.",
        ),
    ),
    "Database query execution failed": HypothesisEvaluationRule(
        pattern=(
            r"sql syntax"
            r"|syntax error.*(sql|query|at or near)"
            r"|query.*(failed|error)"
            r"|operationalerror"
            r"|programmingerror"
        ),
        supporting_message="Database-query failure wording was found",
        weakening_message="No database-query failure wording was found",
        fixes=(
            "Inspect the SQL or ORM query in the stack trace.",
            "Verify table names, columns, parameters, and syntax.",
            "Reproduce the query safely in development.",
        ),
    ),
    "Database deadlock occurred": HypothesisEvaluationRule(
        pattern=(
            r"deadlock detected"
            r"|deadlock found"
            r"|deadlock victim"
            r"|deadlock"
        ),
        supporting_message="Database-deadlock wording was found",
        weakening_message="No database-deadlock wording was found",
        fixes=(
            "Keep transactions short while holding locks.",
            "Access shared rows in a consistent order.",
            "Use bounded retries for deadlock victims.",
        ),
    ),
    "Database lock wait timed out": HypothesisEvaluationRule(
        pattern=(
            r"lock wait timeout"
            r"|lock acquisition.*timeout"
            r"|could not obtain lock"
            r"|database is locked"
        ),
        supporting_message="Database lock-timeout wording was found",
        weakening_message="No database lock-timeout wording was found",
        fixes=(
            "Identify the transaction holding the lock.",
            "Reduce long-running transactions.",
            "Check whether missing indexes lock excessive rows.",
        ),
    ),
    "Transaction serialization conflict occurred": HypothesisEvaluationRule(
        pattern=(
            r"could not serialize access"
            r"|serialization failure"
            r"|concurrent update"
            r"|optimistic lock"
            r"|stale object"
            r"|staleobjectstate"
            r"|version conflict"
        ),
        supporting_message=("Concurrent-transaction conflict wording was found"),
        weakening_message=("No concurrent-transaction conflict wording was found"),
        fixes=(
            "Retry the complete transaction with a bounded policy.",
            "Review whether the isolation level is required.",
            "Use version checks for conflicting updates.",
        ),
    ),
}


CATEGORY_FIXES: dict[str, tuple[str, ...]] = {
    AUTHENTICATION: (
        "Check the Authorization header and token lifecycle.",
        "Verify authentication configuration and credentials.",
    ),
    AUTHORIZATION: (
        "Check the user's roles, permissions, and token scopes.",
        "Verify the endpoint's access-control policy.",
    ),
    VALIDATION: (
        "Compare the request with the documented schema.",
        "Validate required fields, data types, and formats.",
    ),
    SERVER_ERROR: (
        "Inspect application logs and the stack trace.",
        "Review recent code changes near the endpoint.",
    ),
    DATABASE: (
        "Inspect database logs and database exceptions.",
        "Check connectivity, constraints, and queries.",
    ),
    DATABASE_CONCURRENCY: (
        "Inspect active transactions, locks, and wait events.",
        "Review transaction duration, lock order, and retries.",
    ),
    UNKNOWN: (
        "Collect the status code, error message, and stack trace.",
        "Add logging around the failed request.",
    ),
}
