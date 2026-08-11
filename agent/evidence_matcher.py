import re

from .hypothesis import Hypothesis
from .rules import (
    COMPETING_EVIDENCE_PENALTY,
    HYPOTHESIS_EVALUATION_RULES,
)
from .state import AgentState


class EvidenceMatcher:
    """
    Find supporting evidence for generated hypotheses.
    """

    def match(self, state: AgentState) -> AgentState:
        """
        Apply configured evidence rules to relevant hypotheses.
        """

        error_message = state.get("error_message") or ""
        stack_trace = state.get("stack_trace") or ""

        text_to_check = f"{error_message} {stack_trace}"

        hypotheses = [
            Hypothesis.from_dict(data) for data in state.get("hypotheses", [])
        ]

        for target_hypothesis in hypotheses:
            rule = HYPOTHESIS_EVALUATION_RULES.get(target_hypothesis.cause)

            # UNKNOWN and generic hypotheses may have no rule.
            if rule is None:
                continue

            evidence_found = re.search(
                rule.pattern,
                text_to_check,
                re.IGNORECASE,
            )

            if not evidence_found:
                continue

            for hypothesis in hypotheses:
                if hypothesis.cause == target_hypothesis.cause:
                    hypothesis.add_evidence(
                        message=rule.supporting_message,
                        supports=True,
                        weight=rule.support_weight,
                    )
                else:
                    hypothesis.add_evidence(
                        message=(
                            f"Evidence supports '{target_hypothesis.cause}' instead"
                        ),
                        supports=False,
                        weight=(COMPETING_EVIDENCE_PENALTY),
                    )

        hypotheses.sort(
            key=lambda hypothesis: hypothesis.score,
            reverse=True,
        )

        state["hypotheses"] = [hypothesis.to_dict() for hypothesis in hypotheses]

        return state
