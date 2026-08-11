from .graph import run_debugger_graph
from .state import AgentState


class DebuggerWorkflow:
    """provides one public interface for running the debugging workflow"""

    def run(self, initial_state: AgentState) -> AgentState:
        return run_debugger_graph(initial_state)
