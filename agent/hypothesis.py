from dataclasses import dataclass, field
from typing import Dict, List, Any

from .state import AgentState


@dataclass
class Hypothesis:
    """
    One possible explanation for an API failure.
    """

    cause: str
    category: str
    score: float

    supporting_evidence: List[str] = field(default_factory=list)
    weakening_evidence: List[str] = field(default_factory=list)

    
    def add_evidence(
        self ,
        message: str ,
        supports : bool ,
        weight: float ,
    ) -> None :
        
        """
        Add evidence and adjust the current score
        supports=True -> score badhega
        supports=False -> score kam hoga
        """
        
        if supports :
            self.supporting_evidence.append(message)
            self.score = min(self.score+weight, 1.0)
        else :
            self.weakening_evidence.append(message)
            self.score = max(self.score-weight, 0.0)
        

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Hypothesis object into a normal dictionary.
        """
        return {
            "cause": self.cause,
            "category": self.category,
            "score": self.score,
            "supporting_evidence": self.supporting_evidence,
            "weakening_evidence": self.weakening_evidence,
        }
        
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        """
        Rebuild a Hypothesis object from a dictionary.
        """
        
        return cls (
            cause = data["cause"] ,
            category = data["category"] ,
            score = float(data["score"]) ,
            supporting_evidence = list(
                data.get("supporting_evidence", [])
            ) ,
            weakening_evidence = list(
                data.get("weakening_evidence", [])
            ) ,
        )


class HypothesisGenerator:
    """
    Creates possible causes after the failure category is known.
    """

    HYPOTHESIS_TEMPLATES = {
        "AUTHENTICATION": [
            ("JWT token has expired", 0.60),
            ("Authorization header is missing or malformed", 0.50),
            ("Token signature verification failed", 0.40),
        ],
        "VALIDATION": [
            ("Required field is missing from request", 0.70),
            ("Field type mismatch", 0.60),
            ("Field format validation failed", 0.50),
        ],
        "SERVER_ERROR": [
            ("Null pointer dereference", 0.60),
            ("Undefined variable or method call", 0.50),
            ("Unhandled exception in application code", 0.40),
        ],
        "UNKNOWN": [
            ("Insufficient information to identify the root cause", 0.20),
        ],
    }

    def generate(self, state: AgentState) -> AgentState:
        """
        Read the category from state, create matching hypotheses,
        and add them to the state.
        """
        failure_type = state.get("failure_type", "UNKNOWN")

        templates = self.HYPOTHESIS_TEMPLATES.get(
            failure_type,
            self.HYPOTHESIS_TEMPLATES["UNKNOWN"],
        )

        hypotheses = []

        for cause, initial_score in templates:
            hypothesis = Hypothesis(
                cause=cause,
                category=failure_type,
                score=initial_score,
            )

            hypotheses.append(hypothesis)

        # Highest starting score first.
        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        # Store dictionaries in state, not Hypothesis objects.
        state["hypotheses"] = [
            hypothesis.to_dict()
            for hypothesis in hypotheses
        ]

        return state