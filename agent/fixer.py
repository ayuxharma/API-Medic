from .rules import (
    CATEGORY_FIXES,
    HYPOTHESIS_EVALUATION_RULES,
    UNKNOWN,
)
from .state import AgentState


class FixSuggester:
    """
    Generate practical fixes for the selected root cause.
    """

    def suggest(self, state: AgentState) -> AgentState:
        """
        Use cause-specific fixes or category fallback fixes.
        """

        root_cause = state.get(
            "root_cause",
            "",
        )

        failure_type = state.get(
            "failure_type",
            UNKNOWN,
        )

        evaluation_rule = HYPOTHESIS_EVALUATION_RULES.get(root_cause)

        if evaluation_rule is not None and evaluation_rule.fixes:
            fixes = evaluation_rule.fixes
        else:
            fixes = CATEGORY_FIXES.get(
                failure_type,
                CATEGORY_FIXES[UNKNOWN],
            )

        state["suggested_fixes"] = list(fixes)

        return state
