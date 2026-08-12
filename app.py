import argparse

from agent.input_parser import FileInputParser
from agent.logging_config import configure_logging
from agent.state import AgentState
from agent.workflow import DebuggerWorkflow


def parse_arguments() -> argparse.Namespace:
    """
    Define and read command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Analyze API failures using deterministic rules with optional LLM fallback"
        )
    )

    # The user must provide either a file or a direct error message.
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "--file",
        help="Path to a structured API error file",
    )

    input_group.add_argument(
        "--error",
        help="Error message returned by the API",
    )

    parser.add_argument(
        "--endpoint",
        default="Not provided",
        help="API endpoint, for example: /api/login",
    )

    parser.add_argument(
        "--method",
        default="GET",
        help="HTTP method, for example: GET or POST",
    )

    parser.add_argument(
        "--status",
        type=int,
        default=None,
        help="HTTP status code, for example: 401",
    )

    parser.add_argument(
        "--stack-trace",
        default="",
        help="Optional stack trace",
    )

    return parser.parse_args()


def build_state(
    args: argparse.Namespace,
) -> AgentState:
    """
    Convert direct command-line arguments into AgentState.
    """

    if args.error is None:
        raise ValueError("An error message is required in direct-input mode")

    # Validate the status code before starting the workflow.
    if args.status is not None and not 100 <= args.status <= 599:
        raise ValueError("HTTP status code must be between 100 and 599")

    return {
        "endpoint": args.endpoint.strip() or "Not provided",
        "method": args.method.strip().upper(),
        "status_code": args.status,
        "error_message": args.error.strip(),
        "stack_trace": args.stack_trace,
    }


def load_initial_state(
    args: argparse.Namespace,
) -> AgentState:
    """
    Select either file input or direct command-line input.
    """

    if args.file:
        file_parser = FileInputParser()
        return file_parser.parse(args.file)

    return build_state(args)


def print_request_details(state: AgentState) -> None:
    """
    Print the original API request information.
    """

    print("\nRequest details:")
    print(
        "-",
        f"Endpoint: {state.get('endpoint', 'Not provided')}",
    )
    print(
        "-",
        f"Method: {state.get('method', 'Not provided')}",
    )
    print(
        "-",
        f"Status code: {state.get('status_code')}",
    )


def print_classification(state: AgentState) -> None:
    """
    Print the selected failure category and its signals.
    """

    print("\nFailure category:")
    print(
        "-",
        state.get("failure_type", "UNKNOWN"),
    )

    print("\nClassification signals:")

    signals = state.get("signals", [])

    if not signals:
        print("- No classification signals found")
        return

    for signal in signals:
        print("-", signal)


def print_hypotheses(state: AgentState) -> None:
    """
    Print every ranked hypothesis and its evidence.
    """

    print("\nAll hypotheses after evidence and elimination:")

    hypotheses = state.get("hypotheses", [])

    if not hypotheses:
        print("- No hypotheses available")
        return

    for index, hypothesis in enumerate(
        hypotheses,
        start=1,
    ):
        print(f"\n{index}. {hypothesis['cause']} (score: {hypothesis['score']:.2f})")

        supporting_evidence = hypothesis.get(
            "supporting_evidence",
            [],
        )

        weakening_evidence = hypothesis.get(
            "weakening_evidence",
            [],
        )

        for evidence in supporting_evidence:
            print(f"   + {evidence}")

        for evidence in weakening_evidence:
            print(f"   - {evidence}")


def print_root_cause(state: AgentState) -> None:
    """
    Print the final root cause and confidence score.
    """

    print("\n" + "-" * 60)
    print("MOST LIKELY ROOT CAUSE")

    root_cause = state.get(
        "root_cause",
        "Unable to determine the root cause",
    )

    confidence_score = state.get(
        "confidence_score",
        0.0,
    )

    print("-", root_cause)
    print(
        "-",
        f"Confidence score: {confidence_score:.2f}",
    )


def print_routing_details(state: AgentState) -> None:
    """
    Explain which LangGraph branch produced the result.
    """

    analysis_route = state.get(
        "analysis_route",
        "RULE_BASED",
    )

    routing_reason = state.get(
        "routing_reason",
        "Routing information was not provided",
    )

    llm_used = state.get(
        "llm_used",
        False,
    )

    llm_status_message = state.get(
        "llm_status_message",
        "",
    )

    if llm_status_message:
        print(
            "-",
            f"LLM status: {llm_status_message}",
        )

    print("\nAnalysis routing:")
    print(
        "-",
        f"Selected route: {analysis_route}",
    )
    print(
        "-",
        f"Reason: {routing_reason}",
    )
    print(
        "-",
        f"LLM used: {'Yes' if llm_used else 'No'}",
    )

    llm_explanation = state.get(
        "llm_explanation",
        "",
    )

    # Only display this section after successful LLM analysis.
    if llm_used and llm_explanation:
        print("\nLLM explanation:")
        print("-", llm_explanation)


def print_alternative_causes(state: AgentState) -> None:
    """
    Print lower-ranked deterministic causes.
    """

    print("\nAlternative causes:")

    alternative_causes = state.get(
        "alternative_causes",
        [],
    )

    if not alternative_causes:
        print("- No alternative causes available")
        return

    for alternative in alternative_causes:
        print(
            f"- {alternative['cause']} "
            f"(score: {alternative['score']:.2f}, "
            f"relative share: "
            f"{alternative['relative_share']:.1f}%)"
        )


def print_suggested_fixes(state: AgentState) -> None:
    """
    Print deterministic or LLM-generated fixes.
    """

    print("\nSuggested fixes:")

    suggested_fixes = state.get(
        "suggested_fixes",
        [],
    )

    if not suggested_fixes:
        print("- No fix suggestions available")
        return

    for number, fix in enumerate(
        suggested_fixes,
        start=1,
    ):
        print(f"{number}. {fix}")


def print_results(state: AgentState) -> None:
    """
    Print the complete API diagnosis report.
    """

    print("\n" + "=" * 60)
    print("API DEBUGGER RESULT")
    print("=" * 60)

    print_request_details(state)
    print_classification(state)
    print_hypotheses(state)
    print_root_cause(state)
    print_routing_details(state)
    print_alternative_causes(state)
    print_suggested_fixes(state)

    print("\n" + "=" * 60)


def main() -> int:
    """
    Load input, execute the workflow, and print the result.

    Returns:
        0 when diagnosis succeeds.
        2 when input loading fails.
    """
    configure_logging()
    args = parse_arguments()

    try:
        state = load_initial_state(args)
    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        print(f"\nInput error: {error}")
        return 2

    workflow = DebuggerWorkflow()
    result = workflow.run(state)

    print_results(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
