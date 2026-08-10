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
    ]

    def match(self, state: AgentState) -> AgentState:
        """
        Apply evidence rules to hypotheses already stored in state.
        """

        error_message = state.get("error_message") or ""
        stack_trace = state.get("stack_trace") or ""

        text_to_check = f"{error_message} {stack_trace}"

        hypotheses = [
            Hypothesis.from_dict(data)
            for data in state.get("hypotheses", [])
        ]

        for rule in self.EVIDENCE_RULES:
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

        # These lines must be outside both loops.
        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        state["hypotheses"] = [
            hypothesis.to_dict()
            for hypothesis in hypotheses
        ]

        # This must always run, even when no evidence matches.
        return state