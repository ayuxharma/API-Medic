from typing import Literal, cast

from langgraph.graph import END, START, StateGraph

from .classifier import FailureClassifier
from .eliminator import HypothesisEliminator
from .evidence_matcher import EvidenceMatcher
from .fixer import FixSuggester
from .hypothesis import HypothesisGenerator
from .reasoner import RootCauseReasoner
from .rules import UNKNOWN
from .state import AgentState

# A known rule-based result must reach this score to avoid LLM fallback.
MIN_RULE_CONFIDENCE_SCORE = 0.65

# Internal branch names returned by the routing function.
RouteKey = Literal[
    "rule_based",
    "llm_fallback",
]


# These components are stateless, so one reusable instance is enough.
_classifier = FailureClassifier()
_generator = HypothesisGenerator()
_matcher = EvidenceMatcher()
_eliminator = HypothesisEliminator()
_reasoner = RootCauseReasoner()
_fixer = FixSuggester()


def classify_failure(state: AgentState) -> AgentState:
    """Classify the API failure into a broad category."""

    # Avoid mutating LangGraph's input state directly.
    return _classifier.classify(state.copy())


def generate_hypotheses(state: AgentState) -> AgentState:
    """Generate possible causes for the classified failure."""

    return _generator.generate(state.copy())


def match_evidence(state: AgentState) -> AgentState:
    """Increase scores when supporting evidence is found."""

    return _matcher.match(state.copy())


def eliminate_hypotheses(state: AgentState) -> AgentState:
    """Reduce scores when expected evidence is absent."""

    return _eliminator.eliminate(state.copy())


def reason_root_cause(state: AgentState) -> AgentState:
    """Rank hypotheses and select the strongest root cause."""

    return _reasoner.reason(state.copy())


def choose_analysis_route(state: AgentState) -> RouteKey:
    """
    Decide whether rule-based reasoning is sufficient.

    This function only makes a decision. It does not modify state.
    """

    failure_type = state.get("failure_type", UNKNOWN)
    confidence_score = state.get("confidence_score", 0.0)

    # UNKNOWN results should receive deeper analysis.
    if failure_type == UNKNOWN:
        return "llm_fallback"

    # Weak known-category results should also use fallback analysis.
    if confidence_score < MIN_RULE_CONFIDENCE_SCORE:
        return "llm_fallback"

    return "rule_based"


def mark_rule_based_route(state: AgentState) -> AgentState:
    """Record that deterministic analysis was sufficient."""

    updated_state = state.copy()
    confidence_score = state.get("confidence_score", 0.0)

    updated_state["analysis_route"] = "RULE_BASED"
    updated_state["routing_reason"] = (
        f"Rule-based score {confidence_score:.2f} meets the "
        f"required threshold of {MIN_RULE_CONFIDENCE_SCORE:.2f}"
    )
    updated_state["llm_used"] = False

    return updated_state


def mark_llm_fallback_route(state: AgentState) -> AgentState:
    """Record why deeper LLM analysis is required."""

    updated_state = state.copy()
    failure_type = state.get("failure_type", UNKNOWN)
    confidence_score = state.get("confidence_score", 0.0)

    if failure_type == UNKNOWN:
        reason = "Rule-based classification returned UNKNOWN"
    else:
        reason = (
            f"Rule-based score {confidence_score:.2f} is below the "
            f"required threshold of {MIN_RULE_CONFIDENCE_SCORE:.2f}"
        )

    updated_state["analysis_route"] = "LLM_FALLBACK"
    updated_state["routing_reason"] = reason

    # The route is selected, but the LLM is not connected yet.
    updated_state["llm_used"] = False

    return updated_state


def suggest_fixes(state: AgentState) -> AgentState:
    """Generate fixes for the selected root cause."""

    return _fixer.suggest(state.copy())


# Create a graph that uses AgentState as its shared schema.
_graph_builder = StateGraph(AgentState)

# Register the normal diagnosis stages.
_graph_builder.add_node("classify_failure", classify_failure)
_graph_builder.add_node("generate_hypotheses", generate_hypotheses)
_graph_builder.add_node("match_evidence", match_evidence)
_graph_builder.add_node("eliminate_hypotheses", eliminate_hypotheses)
_graph_builder.add_node("reason_root_cause", reason_root_cause)

# Register the two possible routing branches.
_graph_builder.add_node("mark_rule_based_route", mark_rule_based_route)
_graph_builder.add_node(
    "mark_llm_fallback_route",
    mark_llm_fallback_route,
)

_graph_builder.add_node("suggest_fixes", suggest_fixes)

# Run the shared deterministic analysis stages first.
_graph_builder.add_edge(START, "classify_failure")
_graph_builder.add_edge("classify_failure", "generate_hypotheses")
_graph_builder.add_edge("generate_hypotheses", "match_evidence")
_graph_builder.add_edge("match_evidence", "eliminate_hypotheses")
_graph_builder.add_edge("eliminate_hypotheses", "reason_root_cause")

# Select exactly one branch after reasoning is complete.
_graph_builder.add_conditional_edges(
    "reason_root_cause",
    choose_analysis_route,
    {
        "rule_based": "mark_rule_based_route",
        "llm_fallback": "mark_llm_fallback_route",
    },
)

# Both routes currently finish with deterministic fix suggestions.
_graph_builder.add_edge("mark_rule_based_route", "suggest_fixes")
_graph_builder.add_edge("mark_llm_fallback_route", "suggest_fixes")
_graph_builder.add_edge("suggest_fixes", END)

# Compile the graph once so it can be reused for every diagnosis.
debugger_graph = _graph_builder.compile()


def run_debugger_graph(initial_state: AgentState) -> AgentState:
    """Run one API diagnosis through the compiled graph."""

    result = debugger_graph.invoke(initial_state.copy())

    # LangGraph's invoke result is dynamically typed.
    return cast(AgentState, result)
