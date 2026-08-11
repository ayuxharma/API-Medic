import re

from .hypothesis import Hypothesis
from .state import AgentState


class EvidenceMatcher:
    """
    Finds concrete clues in the error message and stack trace,
    then adjusts hypothesis scores.
    """

    EVIDENCE_RULES = [
        {
            "pattern": r"(jwt|token).*(expired|expiration)",
            "cause": "JWT token has expired",
            "message": "Token-expiration wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"(authorization|auth).*(missing|absent|required)"
                r"|missing.*(authorization|auth)"
            ),
            "cause": "Authorization header is missing or malformed",
            "message": "Authorization-header absence was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"signature.*(invalid|failed|verification)"
                r"|invalid.*signature"
            ),
            "cause": "Token signature verification failed",
            "message": "Token-signature failure wording was found",
            "weight": 0.30,
        },
        {
            "pattern": r"(required|missing).*(field|parameter|email)",
            "cause": "Required field is missing from request",
            "message": "Required or missing request field was found",
            "weight": 0.30,
        },
        {
            "pattern": r"type mismatch|expected.*got|invalid type",
            "cause": "Field type mismatch",
            "message": "Field type-mismatch wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"invalid.*(email|url|date|format)"
                r"|format validation"
            ),
            "cause": "Field format validation failed",
            "message": "Invalid field-format wording was found",
            "weight": 0.30,
        },
        {
            "pattern": r"nullpointer|null pointer|nonetype",
            "cause": "Null pointer dereference",
            "message": "Null-reference wording was found",
            "weight": 0.30,
        },
        {
            "pattern": r"undefined|not defined",
            "cause": "Undefined variable or method call",
            "message": "Undefined-reference wording was found",
            "weight": 0.30,
        },
        {
            "pattern": r"traceback|unhandled exception|exception",
            "cause": "Unhandled exception in application code",
            "message": "Unhandled-exception wording was found",
            "weight": 0.20,
        },
        {
            "pattern": (
                r"permission.*(denied|missing|required|insufficient)"
                r"|(?:denied|missing|insufficient).*permission"
                r"|access denied"
            ),
            "cause": "User lacks required permission",
            "message": "Permission-denial wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"insufficient.*scope"
                r"|scope.*(missing|required|insufficient)"
            ),
            "cause": "Token has insufficient scope",
            "message": "Insufficient token-scope wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"role.*(required|forbidden|denied|not allowed)"
                r"|(?:required|forbidden).*role"
            ),
            "cause": "User role is not allowed for this resource",
            "message": "Role-based access wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"database.*connection.*"
                r"(refused|failed|timeout|unavailable)"
                r"|(?:could not|cannot|failed to).*connect.*"
                r"(database|postgres|postgresql|mysql)"
                r"|too many connections"
        ),
            "cause": "Database connection is unavailable",
            "message": "Database-connection failure wording was found",
            "weight": 0.30,
        },
        {
            "pattern": (
                r"duplicate key"
                r"|unique constraint"
                r"|unique violation"
                r"|foreign key constraint"
                r"|integrityerror"
                r"|not-null constraint"
    ),
            "cause": "Database constraint was violated",
            "message": "Database-constraint violation wording was found",
            "weight": 0.30,
},
{
            "pattern": (
                r"sql syntax"
                r"|syntax error.*(sql|query|at or near)"
                r"|query.*(failed|error)"
                r"|operationalerror"
                r"|programmingerror"
    ),
            "cause": "Database query execution failed",
            "message": "Database-query failure wording was found",
            "weight": 0.30,
},
    ]

    def match(self, state: AgentState) -> AgentState:
        """
        Apply relevant evidence rules to the hypotheses in state.
        """

        error_message = state.get("error_message") or ""
        stack_trace = state.get("stack_trace") or ""

        text_to_check = f"{error_message} {stack_trace}"

        hypotheses = [
            Hypothesis.from_dict(data)
            for data in state.get("hypotheses", [])
        ]

        available_causes = {
            hypothesis.cause
            for hypothesis in hypotheses
        }

        for rule in self.EVIDENCE_RULES:
            # Skip rules belonging to a different failure category.
            if rule["cause"] not in available_causes:
                continue

            evidence_found = re.search(
                rule["pattern"],
                text_to_check,
                re.IGNORECASE,
            )

            if not evidence_found:
                continue

            for hypothesis in hypotheses:
                if hypothesis.cause == rule["cause"]:
                    hypothesis.add_evidence(
                        message=rule["message"],
                        supports=True,
                        weight=rule["weight"],
                    )
                else:
                    hypothesis.add_evidence(
                        message=(
                            f"Evidence supports "
                            f"'{rule['cause']}' instead"
                        ),
                        supports=False,
                        weight=0.15,
                    )

        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        state["hypotheses"] = [
            hypothesis.to_dict()
            for hypothesis in hypotheses
        ]

        return state