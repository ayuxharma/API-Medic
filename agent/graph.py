from typing import Literal, cast

from langgraph.graph import END, START, StateGraph

from .classifier import FailureClassifier
from .eliminator import HypothesisEliminator
from .evidence_matcher import EvidenceMatcher
from .fixer import FixSuggester
from .hypothesis import HypothesisGenerator
from .llm_analyzer import (
    LLMAnalysisError,
    LLMAnalyzer,
)
from .reasoner import RootCauseReasoner
from .rules import UNKNOWN
from .state import AgentState

# Minimum score required to trust a known rule-based result.
MIN_RULE_CONFIDENCE_SCORE = 0.65

# Internal values returned by the conditional routing function.
RouteKey = Literal[
    "rule_based",
    "llm_fallback",
]


# These components do not store request-specific state,
# so one shared instance of each component is sufficient.
_classifier = FailureClassifier()
_generator = HypothesisGenerator()
_matcher = EvidenceMatcher()
_eliminator = HypothesisEliminator()
_reasoner = RootCauseReasoner()
_fixer = FixSuggester()
_llm_analyzer = LLMAnalyzer()


def classify_failure(
    state: AgentState,
) -> AgentState:
    """
    Classify the API failure into a broad category.
    """

    # Copy the state so the input object is not modified directly.
    return _classifier.classify(state.copy())


def generate_hypotheses(
    state: AgentState,
) -> AgentState:
    """
    Generate possible causes for the classified failure.
    """

    return _generator.generate(state.copy())


def match_evidence(
    state: AgentState,
) -> AgentState:
    """
    Increase hypothesis scores when evidence is found.
    """

    return _matcher.match(state.copy())


def eliminate_hypotheses(
    state: AgentState,
) -> AgentState:
    """
    Reduce scores when expected evidence is missing.
    """

    return _eliminator.eliminate(state.copy())


def reason_root_cause(
    state: AgentState,
) -> AgentState:
    """
    Rank hypotheses and select the strongest root cause.
    """

    return _reasoner.reason(state.copy())


def choose_analysis_route(
    state: AgentState,
) -> RouteKey:
    """
    Decide whether deterministic reasoning is sufficient.
    """

    failure_type = state.get(
        "failure_type",
        UNKNOWN,
    )

    confidence_score = state.get(
        "confidence_score",
        0.0,
    )

    # Unknown failures require deeper analysis.
    if failure_type == UNKNOWN:
        return "llm_fallback"

    # Weak known-category results also use fallback analysis.
    if confidence_score < MIN_RULE_CONFIDENCE_SCORE:
        return "llm_fallback"

    return "rule_based"


def mark_rule_based_route(
    state: AgentState,
) -> AgentState:
    """
    Record that deterministic reasoning was sufficient.
    """

    updated_state = state.copy()

    confidence_score = state.get(
        "confidence_score",
        0.0,
    )

    updated_state["analysis_route"] = "RULE_BASED"

    updated_state["routing_reason"] = (
        f"Rule-based score {confidence_score:.2f} meets the "
        f"required threshold of "
        f"{MIN_RULE_CONFIDENCE_SCORE:.2f}"
    )

    # No external model was required.
    updated_state["llm_used"] = False
    updated_state["llm_explanation"] = ""
    updated_state["llm_status_message"] = ""

    return updated_state


def mark_llm_fallback_route(
    state: AgentState,
) -> AgentState:
    """
    Record why the graph selected the LLM fallback route.
    """

    updated_state = state.copy()

    failure_type = state.get(
        "failure_type",
        UNKNOWN,
    )

    confidence_score = state.get(
        "confidence_score",
        0.0,
    )

    if failure_type == UNKNOWN:
        reason = "Rule-based classification returned UNKNOWN"
    else:
        reason = (
            f"Rule-based score {confidence_score:.2f} is below "
            f"the required threshold of "
            f"{MIN_RULE_CONFIDENCE_SCORE:.2f}"
        )

    updated_state["analysis_route"] = "LLM_FALLBACK"
    updated_state["routing_reason"] = reason

    # These fields will be updated if LLM analysis succeeds.
    updated_state["llm_used"] = False
    updated_state["llm_explanation"] = ""
    updated_state["llm_status_message"] = ""

    return updated_state


def analyze_with_llm(
    state: AgentState,
) -> AgentState:
    """
    Apply optional LLM analysis without risking workflow failure.
    """

    updated_state = state.copy()

    try:
        analysis = _llm_analyzer.analyze(updated_state)
    except LLMAnalysisError as error:
        # Preserve the deterministic result if the API call,
        # validation, or structured response processing fails.
        updated_state["llm_used"] = False
        updated_state["llm_explanation"] = ""
        updated_state["llm_status_message"] = str(error)

        return updated_state

    if analysis is None:
        # The route was selected, but LLM usage is disabled
        # or an API key has not been configured.
        updated_state["llm_used"] = False
        updated_state["llm_explanation"] = ""

        updated_state["llm_status_message"] = (
            "LLM fallback is disabled or not configured"
        )

        return updated_state

    # Only validated LLM fields are applied to the state.
    updated_state["root_cause"] = analysis.root_cause

    updated_state["confidence_score"] = analysis.confidence_score

    updated_state["suggested_fixes"] = list(analysis.suggested_fixes)

    updated_state["llm_explanation"] = analysis.explanation

    updated_state["llm_used"] = True

    updated_state["llm_status_message"] = "LLM analysis completed successfully"

    return updated_state


def suggest_fixes(
    state: AgentState,
) -> AgentState:
    """
    Generate fixes unless the LLM already supplied them.
    """

    if state.get("llm_used", False):
        # Preserve the validated fixes returned by the LLM.
        return state.copy()

    # Use deterministic fixes when the LLM was not used
    # or when external analysis failed.
    return _fixer.suggest(state.copy())


# Create a graph using AgentState as its shared schema.
_graph_builder = StateGraph(AgentState)


# Register deterministic diagnosis nodes.
_graph_builder.add_node(
    "classify_failure",
    classify_failure,
)

_graph_builder.add_node(
    "generate_hypotheses",
    generate_hypotheses,
)

_graph_builder.add_node(
    "match_evidence",
    match_evidence,
)

_graph_builder.add_node(
    "eliminate_hypotheses",
    eliminate_hypotheses,
)

_graph_builder.add_node(
    "reason_root_cause",
    reason_root_cause,
)


# Register routing and result-processing nodes.
_graph_builder.add_node(
    "mark_rule_based_route",
    mark_rule_based_route,
)

_graph_builder.add_node(
    "mark_llm_fallback_route",
    mark_llm_fallback_route,
)

_graph_builder.add_node(
    "analyze_with_llm",
    analyze_with_llm,
)

_graph_builder.add_node(
    "suggest_fixes",
    suggest_fixes,
)


# Define the shared deterministic pipeline.
_graph_builder.add_edge(
    START,
    "classify_failure",
)

_graph_builder.add_edge(
    "classify_failure",
    "generate_hypotheses",
)

_graph_builder.add_edge(
    "generate_hypotheses",
    "match_evidence",
)

_graph_builder.add_edge(
    "match_evidence",
    "eliminate_hypotheses",
)

_graph_builder.add_edge(
    "eliminate_hypotheses",
    "reason_root_cause",
)


# Choose exactly one route after deterministic reasoning.
_graph_builder.add_conditional_edges(
    "reason_root_cause",
    choose_analysis_route,
    {
        "rule_based": "mark_rule_based_route",
        "llm_fallback": "mark_llm_fallback_route",
    },
)


# Strong results skip the external LLM entirely.
_graph_builder.add_edge(
    "mark_rule_based_route",
    "suggest_fixes",
)


# Weak or unknown results receive one optional LLM analysis.
_graph_builder.add_edge(
    "mark_llm_fallback_route",
    "analyze_with_llm",
)

_graph_builder.add_edge(
    "analyze_with_llm",
    "suggest_fixes",
)


# Both paths finish after fix suggestions are available.
_graph_builder.add_edge(
    "suggest_fixes",
    END,
)


# Validate and compile the workflow once.
debugger_graph = _graph_builder.compile()


def run_debugger_graph(
    initial_state: AgentState,
) -> AgentState:
    """
    Execute one API diagnosis through LangGraph.
    """

    # Protect the caller's original dictionary.
    result = debugger_graph.invoke(initial_state.copy())

    # LangGraph returns the completed state dynamically.
    return cast(AgentState, result)
