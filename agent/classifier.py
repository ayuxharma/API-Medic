from .rules import (
    CATEGORY_RULES,
    KEYWORD_WEIGHT,
    SERVER_ERROR,
    SERVER_ERROR_MIN_STATUS,
    SERVER_ERROR_STATUS_WEIGHT,
    STATUS_RULES,
    UNKNOWN,
)
from .state import AgentState


class FailureClassifier:
    """
    Read API error details and assign one broad failure category.
    """

    def classify(self, state: AgentState) -> AgentState:
        """
        Score all configured categories and select the best match.
        """

        error_message = (
            state.get("error_message") or ""
        ).lower()

        stack_trace = (
            state.get("stack_trace") or ""
        ).lower()

        status_code = state.get("status_code")

        text_to_check = f"{error_message} {stack_trace}"

        scores = {
            category: 0
            for category in CATEGORY_RULES
        }

        signals: list[str] = []

        self._apply_status_rule(
            status_code=status_code,
            scores=scores,
            signals=signals,
        )

        self._apply_strong_signals(
            text=text_to_check,
            scores=scores,
            signals=signals,
        )

        self._apply_keywords(
            text=text_to_check,
            scores=scores,
            signals=signals,
        )

        best_category = max(
            scores,
            key=scores.get,
        )

        if scores[best_category] == 0:
            state["failure_type"] = UNKNOWN
            signals.append(
                "No known classification signal was found"
            )
        else:
            state["failure_type"] = best_category

        state["signals"] = signals

        return state

    @staticmethod
    def _apply_status_rule(
        status_code: int | None,
        scores: dict[str, int],
        signals: list[str],
    ) -> None:
        """
        Apply exact and generic HTTP status-code rules.
        """

        status_rule = STATUS_RULES.get(status_code)

        if status_rule is not None:
            scores[status_rule.category] += status_rule.weight
            signals.append(status_rule.message)
            return

        if (
            isinstance(status_code, int)
            and status_code >= SERVER_ERROR_MIN_STATUS
        ):
            scores[SERVER_ERROR] += (
                SERVER_ERROR_STATUS_WEIGHT
            )

            signals.append(
                f"HTTP {status_code} indicates "
                f"a server-side failure"
            )

    @staticmethod
    def _apply_strong_signals(
        text: str,
        scores: dict[str, int],
        signals: list[str],
    ) -> None:
        """
        Apply high-confidence category-specific signals.
        """

        for category, rule in CATEGORY_RULES.items():
            for strong_signal in rule.strong_signals:
                if strong_signal not in text:
                    continue

                scores[category] += rule.strong_weight

                signal_label = (
                    category.lower().replace("_", "-")
                )

                signals.append(
                    f"Matched strong {signal_label} signal "
                    f"'{strong_signal}'"
                )

                # One strong signal per category is sufficient.
                break

    @staticmethod
    def _apply_keywords(
        text: str,
        scores: dict[str, int],
        signals: list[str],
    ) -> None:
        """
        Apply ordinary keyword evidence.
        """

        for category, rule in CATEGORY_RULES.items():
            for keyword in rule.keywords:
                if keyword not in text:
                    continue

                scores[category] += KEYWORD_WEIGHT

                signals.append(
                    f"Matched '{keyword}' for {category}"
                )