import re

from .hypothesis import Hypothesis
from .rules import HYPOTHESIS_EVALUATION_RULES
from .state import AgentState


class HypothesisEliminator:
    """
    Reduce scores when expected evidence is absent.
    """

    def eliminate(self, state: AgentState) -> AgentState:
        """
        Apply configured absence penalties.
        """

        error_message = state.get("error_message") or ""
        stack_trace = state.get("stack_trace") or ""

        text_to_check = f"{error_message} {stack_trace}"

        hypotheses = [
            Hypothesis.from_dict(data) for data in state.get("hypotheses", [])
        ]

        for hypothesis in hypotheses:
            rule = HYPOTHESIS_EVALUATION_RULES.get(hypothesis.cause)

            if rule is None:
                continue

            evidence_found = re.search(
                rule.pattern,
                text_to_check,
                re.IGNORECASE,
            )

            if evidence_found:
                continue

            hypothesis.add_evidence(
                message=rule.weakening_message,
                supports=False,
                weight=rule.absence_penalty,
            )

        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        state["hypotheses"] = [hypothesis.to_dict() for hypothesis in hypotheses]

        return state
