import logging
from time import perf_counter

from .graph import run_debugger_graph
from .state import AgentState

logger = logging.getLogger(__name__)


class DebuggerWorkflow:
    """
    Provide one public interface for running the workflow.
    """

    def run(
        self,
        initial_state: AgentState,
    ) -> AgentState:
        """
        Run one diagnosis and record safe operational metadata.
        """

        started_at = perf_counter()

        try:
            result = run_debugger_graph(initial_state)
        except Exception as error:
            duration_ms = (perf_counter() - started_at) * 1000

            # Record only the exception type—not its potentially
            # sensitive message or the original user input.
            logger.error(
                "event=diagnosis_failed error_type=%s duration_ms=%.2f",
                type(error).__name__,
                duration_ms,
            )

            # Let the web or CLI boundary decide how to respond.
            raise

        duration_ms = (perf_counter() - started_at) * 1000

        # Never log error_message, stack_trace, tokens, or keys.
        logger.info(
            "event=diagnosis_completed "
            "failure_type=%s "
            "analysis_route=%s "
            "confidence_score=%.2f "
            "llm_used=%s "
            "duration_ms=%.2f",
            result.get(
                "failure_type",
                "UNKNOWN",
            ),
            result.get(
                "analysis_route",
                "RULE_BASED",
            ),
            result.get(
                "confidence_score",
                0.0,
            ),
            result.get(
                "llm_used",
                False,
            ),
            duration_ms,
        )

        return result
