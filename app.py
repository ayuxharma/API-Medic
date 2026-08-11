import argparse

from agent.input_parser import FileInputParser
from agent.state import AgentState
from agent.workflow import DebuggerWorkflow


def parse_arguments() -> argparse.Namespace:
    """
    Define and read command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Rule-based API Failure Debugger")

    # The user must provide either --file or --error,
    # but cannot provide both at the same time.
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

    This function is used when the user provides --error
    instead of --file.
    """

    if args.error is None:
        raise ValueError("An error message is required in direct-input mode")

    return {
        "endpoint": args.endpoint,
        "method": args.method.upper(),
        "status_code": args.status,
        "error_message": args.error,
        "stack_trace": args.stack_trace,
    }


def load_initial_state(
    args: argparse.Namespace,
) -> AgentState:
    """
    Select the correct input source.

    File mode:
        Parse the file using FileInputParser.

    Direct mode:
        Build state from command-line arguments.
    """
    if args.file:
        file_parser = FileInputParser()
        return file_parser.parse(args.file)

    return build_state(args)


def print_results(state: AgentState) -> None:
    """
    Print the complete debugging report.
    """
    print("\n" + "=" * 60)
    print("API DEBUGGER RESULT")
    print("=" * 60)

    print("\nRequest details:")
    print("-", f"Endpoint: {state['endpoint']}")
    print("-", f"Method: {state['method']}")
    print("-", f"Status code: {state['status_code']}")

    print("\nFailure category:")
    print("-", state["failure_type"])

    print("\nClassification signals:")

    signals = state.get("signals", [])

    if not signals:
        print("- No classification signals found")

    for signal in signals:
        print("-", signal)

    print("\nAll hypotheses after evidence and elimination:")

    hypotheses = state.get("hypotheses", [])

    if not hypotheses:
        print("- No hypotheses available")

    for index, hypothesis in enumerate(
        hypotheses,
        start=1,
    ):
        print(f"\n{index}. {hypothesis['cause']} (score: {hypothesis['score']})")

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

    print("\n" + "-" * 60)
    print("MOST LIKELY ROOT CAUSE")

    print(
        "-",
        state.get(
            "root_cause",
            "Unable to determine the root cause",
        ),
    )

    confidence_score = state.get(
        "confidence_score",
        0.0,
    )

    print("-", f"Evidence score: {confidence_score}")

    print("\nAlternative causes:")

    alternative_causes = state.get(
        "alternative_causes",
        [],
    )

    if not alternative_causes:
        print("- No alternative causes available")

    for alternative in alternative_causes:
        print(
            f"- {alternative['cause']} "
            f"(score: {alternative['score']}, "
            f"relative share: "
            f"{alternative['relative_share']}%)"
        )

    print("\nSuggested fixes:")

    suggested_fixes = state.get(
        "suggested_fixes",
        [],
    )

    if not suggested_fixes:
        print("- No fix suggestions available")

    for number, fix in enumerate(
        suggested_fixes,
        start=1,
    ):
        print(f"{number}. {fix}")

    print("\n" + "=" * 60)


def main() -> int:
    """
    Main application entry point.

    Returns:
        0 when analysis succeeds.
        2 when input loading fails.
    """
    args = parse_arguments()

    try:
        state = load_initial_state(args)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"\nInput error: {error}")
        return 2

    workflow = DebuggerWorkflow()
    result = workflow.run(state)

    print_results(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
