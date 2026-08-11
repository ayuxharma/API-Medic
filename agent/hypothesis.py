from dataclasses import dataclass, field
from typing import Any

from .rules import HYPOTHESIS_TEMPLATES, UNKNOWN
from .state import AgentState


@dataclass
class Hypothesis:
    """
    One possible explanation for an API failure.
    """

    cause: str
    category: str
    score: float

    supporting_evidence: list[str] = field(
        default_factory=list
    )

    weakening_evidence: list[str] = field(
        default_factory=list
    )

    def add_evidence(
        self,
        message: str,
        supports: bool,
        weight: float,
    ) -> None:
        """
        Add evidence and adjust the current hypothesis score.
        """

        if supports:
            self.supporting_evidence.append(message)

            self.score = min(
                self.score + weight,
                1.0,
            )

        else:
            self.weakening_evidence.append(message)

            self.score = max(
                self.score - weight,
                0.0,
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the hypothesis into a serializable dictionary.
        """

        return {
            "cause": self.cause,
            "category": self.category,
            "score": round(self.score, 2),
            "supporting_evidence": list(
                self.supporting_evidence
            ),
            "weakening_evidence": list(
                self.weakening_evidence
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Hypothesis":
        """
        Rebuild a Hypothesis object from a dictionary.
        """

        return cls(
            cause=data["cause"],
            category=data["category"],
            score=float(data["score"]),
            supporting_evidence=list(
                data.get("supporting_evidence", [])
            ),
            weakening_evidence=list(
                data.get("weakening_evidence", [])
            ),
        )


class HypothesisGenerator:
    """
    Create hypotheses for the classified failure category.
    """

    def generate(self, state: AgentState) -> AgentState:
        """
        Generate configured hypotheses and add them to state.
        """

        failure_type = state.get(
            "failure_type",
            UNKNOWN,
        )

        templates = HYPOTHESIS_TEMPLATES.get(
            failure_type,
            HYPOTHESIS_TEMPLATES[UNKNOWN],
        )

        hypotheses = [
            Hypothesis(
                cause=template.cause,
                category=failure_type,
                score=template.initial_score,
            )
            for template in templates
        ]

        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        state["hypotheses"] = [
            hypothesis.to_dict()
            for hypothesis in hypotheses
        ]

        return state