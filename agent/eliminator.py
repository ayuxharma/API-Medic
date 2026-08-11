import re

from .hypothesis import Hypothesis
from .state import AgentState

class HypothesisEliminator:
    """
    Reduces the score of hypotheses whose expected evidence is absent.
    """

    ELIMINATION_RULES = {
        "JWT token has expired": {
            "pattern": r"(jwt|token).*(expired|expiration)",
            "message": "No token-expiration wording was found",
            "penalty": 0.10,
        },
        "Authorization header is missing or malformed": {
            "pattern": r"(authorization|auth).*(missing|absent|required)|missing.*(authorization|auth)",
            "message": "No missing Authorization-header wording was found",
            "penalty": 0.10,
        },
        "Token signature verification failed": {
            "pattern": r"signature.*(invalid|failed|verification)|invalid.*signature",
            "message": "No token-signature failure wording was found",
            "penalty": 0.10,
        },
        "Required field is missing from request": {
            "pattern": r"(required|missing).*(field|parameter|email)",
            "message": "No required or missing field wording was found",
            "penalty": 0.10,
        },
        "Field type mismatch": {
            "pattern": r"type mismatch|expected.*got|invalid type",
            "message": "No field type-mismatch wording was found",
            "penalty": 0.10,
        },
        "Field format validation failed": {
            "pattern": r"invalid.*(email|url|date|format)|format validation",
            "message": "No invalid field-format wording was found",
            "penalty": 0.10,
        },
        "Null pointer dereference": {
            "pattern": r"nullpointer|null pointer|nonetype",
            "message": "No null-reference wording was found",
            "penalty": 0.10,
        },
        "Undefined variable or method call": {
            "pattern": r"undefined|not defined",
            "message": "No undefined-reference wording was found",
            "penalty": 0.10,
        },
        "Unhandled exception in application code": {
            "pattern": r"traceback|unhandled exception|exception",
            "message": "No unhandled-exception wording was found",
            "penalty": 0.10,
        },
        "User lacks required permission": {
    "pattern": (
        r"permission.*(denied|missing|required|insufficient)"
        r"|(?:denied|missing|insufficient).*permission"
        r"|access denied"
    ),
    "message": "No permission-denial wording was found",
    "penalty": 0.10,
},
"Token has insufficient scope": {
    "pattern": (
        r"insufficient.*scope"
        r"|scope.*(missing|required|insufficient)"
    ),
    "message": "No insufficient-scope wording was found",
    "penalty": 0.10,
},
"User role is not allowed for this resource": {
    "pattern": (
        r"role.*(required|forbidden|denied|not allowed)"
        r"|(?:required|forbidden).*role"
    ),
    "message": "No role-based access wording was found",
    "penalty": 0.10,
},
"Database connection is unavailable": {
    "pattern": (
        r"database.*connection.*"
        r"(refused|failed|timeout|unavailable)"
        r"|(?:could not|cannot|failed to).*connect.*"
        r"(database|postgres|postgresql|mysql)"
        r"|too many connections"
    ),
    "message": (
        "No database-connection failure wording was found"
    ),
    "penalty": 0.10,
},
"Database constraint was violated": {
    "pattern": (
        r"duplicate key"
        r"|unique constraint"
        r"|unique violation"
        r"|foreign key constraint"
        r"|integrityerror"
        r"|not-null constraint"
    ),
    "message": (
        "No database-constraint violation wording was found"
    ),
    "penalty": 0.10,
},
"Database query execution failed": {
    "pattern": (
        r"sql syntax"
        r"|syntax error.*(sql|query|at or near)"
        r"|query.*(failed|error)"
        r"|operationalerror"
        r"|programmingerror"
    ),
    "message": (
        "No database-query failure wording was found"
    ),
    "penalty": 0.10,
},
    }
    
    def eliminate (self, state: AgentState) -> AgentState:
        """
        Apply soft-elimination rules to existing hypotheses.
        """
        
        error_message = (state.get("error_message") or "")
        stack_trace = (state.get("stack_trace") or "")
        text_to_check = f"{error_message} {stack_trace}"
        
        hypotheses = [
            Hypothesis.from_dict(data)
            for data in state.get("hypotheses", [])
        ]
        
        for hypothesis in hypotheses:
            rule = self.ELIMINATION_RULES.get(hypothesis.cause)
            
            # some generic hypotheses may not need elimination rules
            if rule is None:
                continue
            
            evidence_found = re.search(
                rule["pattern"], 
                text_to_check, 
                re.IGNORECASE)
            
            if not evidence_found:
                hypothesis.add_evidence(
                    message = rule["message"] ,
                    supports=False ,
                    weight = rule["penalty"] ,
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