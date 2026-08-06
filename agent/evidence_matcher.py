import re

from .hypothesis import Hypothesis
from .state import AgentState

class EvidenceMatcher :
    """
    Looks for concrete clues in the error message and stack trace.
    """
    EVIDENCE_RULES = [
        {
            "pattern" : r"(jwt|token).*(expired|expiration)" ,
            "cause" : "JWT token has expired" ,
            "message" : "Token-expiration wording was found" ,
            "weight" : 0.30 ,
        } ,
        {
            "pattern": r"(authorization|auth).*(missing|absent|required)|missing.*(authorization|auth)",
            "cause": "Authorization header is missing or malformed",
            "message": "Authorization-header absence was found",
            "weight": 0.30,
        },
        {
            "pattern": r"signature.*(invalid|failed|verification)|invalid.*signature",
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
            "message": "Field type mismatch wording was found",
            "weight": 0.30,
        },
        {
            "pattern": r"invalid.*(email|url|date|format)|format validation",
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
        Check the error message and stack trace for evidence.
        """
        
        error_message = (state.get("error_message") or "").lower()
        stack_trace = (state.get("stack_trace") or "").lower()
        text_to_check = f"{error_message} {stack_trace}"

        # state stores dictonaries, so rebuild usable hypothesis objects from them
        hypotheses = [
            Hypothesis.from_dict(data)
            for data in state.get("hypotheses", [])
        ]
        
        for rule in self.EVIDENCE_RULES:
            pattern_found = re.search(
                rule["pattern"] ,
                text_to_check ,
                re.IGNORECASE ,
            )
            
            if not pattern_found:
                continue
            
            for hypothesis in hypotheses:
                if hypothesis.cause == rule["cause"]:
                    hypothesis.add_evidence(
                        message=rule["message"],
                        supports=True,
                        weight=rule["weight"],
                    )
                else :
                    hypothesis.add_evidence(
                        message = (
                            f"Evidence supports "
                            f"'{rule['cause']}' instead"
                        ) ,
                        supports = False ,
                        weight = 0.15 ,
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