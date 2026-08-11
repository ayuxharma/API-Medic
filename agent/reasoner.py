from .state import (
    AgentState,
    AlternativeCauseData,
    HypothesisData,
)


class RootCauseReasoner:
    """
    Select the strongest existing hypothesis as the root cause.
    """

    def reason(self, state: AgentState) -> AgentState:
        """
        Rank hypotheses and store the final reasoning result.
        """

        hypotheses: list[HypothesisData] = state.get(
            "hypotheses",
            [],
        )

        hypotheses.sort(
            key=lambda hypothesis: hypothesis["score"],
            reverse=True,
        )

        state["hypotheses"] = hypotheses

        if not hypotheses:
            state["root_cause"] = "Unable to determine the root cause"

            state["confidence_score"] = 0.0
            state["alternative_causes"] = []

            return state

        primary = hypotheses[0]

        state["root_cause"] = primary["cause"]
        state["confidence_score"] = primary["score"]

        total_score = sum(hypothesis["score"] for hypothesis in hypotheses)

        alternatives: list[AlternativeCauseData] = []

        for hypothesis in hypotheses[1:4]:
            relative_share = 0.0

            if total_score > 0:
                relative_share = round(
                    (hypothesis["score"] / total_score) * 100,
                    1,
                )

            alternative: AlternativeCauseData = {
                "cause": hypothesis["cause"],
                "score": hypothesis["score"],
                "relative_share": relative_share,
            }

            alternatives.append(alternative)

        state["alternative_causes"] = alternatives

        return state
