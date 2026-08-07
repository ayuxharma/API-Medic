import argparse

from agent.classifier import FailureClassifier
from agent.eliminator import HypothesisEliminator
from agent.evidence_matcher import EvidenceMatcher
from agent.fixer import FixSuggester
from agent.hypothesis import HypothesisGenerator
from agent.reasoner import RootCauseReasoner
from agent.state import AgentState


def parse_arguments():
    """Read command-line arguments given by the user."""

    parser = argparse.ArgumentParser(
        description="Rule-based API Failure Debugger"
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
        "--error",
        required=True,
        help="Error message returned by the API",
    )

    parser.add_argument(
        "--stack-trace",
        default="",
        help="Optional stack trace",
    )

    return parser.parse_args()


def build_state(args) -> AgentState:
    """Convert CLI arguments into shared application state."""

    return {
        "endpoint": args.endpoint,
        "method": args.method.upper(),
        "status_code": args.status,
        "error_message": args.error,
        "stack_trace": args.stack_trace,
    }


def print_results(state: AgentState) -> None:
    """Print the final debugging report."""

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
    for signal in state["signals"]:
        print("-", signal)

    print("\nAll hypotheses after evidence and elimination:")

    for index, hypothesis in enumerate(state["hypotheses"], start=1):
        print(
            f"\n{index}. {hypothesis['cause']} "
            f"(score: {hypothesis['score']})"
        )

        for evidence in hypothesis["supporting_evidence"]:
            print(f"   + {evidence}")

        for evidence in hypothesis["weakening_evidence"]:
            print(f"   - {evidence}")

    print("\n" + "-" * 60)
    print("MOST LIKELY ROOT CAUSE")
    print("-", state["root_cause"])
    print("-", f"Evidence score: {state['confidence_score']}")

    print("\nAlternative causes:")

    if not state["alternative_causes"]:
        print("- No alternative causes available")

    for alternative in state["alternative_causes"]:
        print(
            f"- {alternative['cause']} "
            f"(score: {alternative['score']}, "
            f"relative share: {alternative['relative_share']}%)"
        )

    print("\nSuggested fixes:")

    for number, fix in enumerate(state["suggested_fixes"], start=1):
        print(f"{number}. {fix}")

    print("\n" + "=" * 60)


def main():
    args = parse_arguments()
    state = build_state(args)

    classifier = FailureClassifier()
    generator = HypothesisGenerator()
    matcher = EvidenceMatcher()
    eliminator = HypothesisEliminator()
    reasoner = RootCauseReasoner()
    fixer = FixSuggester()

    state = classifier.classify(state)
    state = generator.generate(state)
    state = matcher.match(state)
    state = eliminator.eliminate(state)
    state = reasoner.reason(state)
    state = fixer.suggest(state)

    print_results(state)


if __name__ == "__main__":
    main()