from agent.classifier import FailureClassifier
from agent.eliminator import HypothesisEliminator
from agent.evidence_matcher import EvidenceMatcher
from agent.hypothesis import HypothesisGenerator
from agent.reasoner import RootCauseReasoner
from agent.state import AgentState


def main():
    # Temporary hard-coded input for testing.
    state: AgentState = {
        "status_code": 401,
        "error_message": "JWT token expired",
        "stack_trace": "",
    }

    # Create one object for each pipeline stage.
    classifier = FailureClassifier()
    generator = HypothesisGenerator()
    matcher = EvidenceMatcher()
    eliminator = HypothesisEliminator()
    reasoner = RootCauseReasoner()

    # Run the complete pipeline in the correct order.
    state = classifier.classify(state)
    state = generator.generate(state)
    state = matcher.match(state)
    state = eliminator.eliminate(state)
    state = reasoner.reason(state)

    # Print classification result.
    print("\n" + "=" * 60)
    print("API DEBUGGER RESULT")
    print("=" * 60)

    print("\nFailure category:")
    print("-", state["failure_type"])

    print("\nClassification signals:")
    for signal in state["signals"]:
        print("-", signal)

    # Print every considered hypothesis.
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

    # Print final conclusion from the reasoner.
    print("\n" + "-" * 60)
    print("MOST LIKELY ROOT CAUSE")
    print("-", state["root_cause"])
    print("-", f"Evidence score: {state['confidence_level']}")

    print("\nAlternative causes:")

    if not state["alternative_causes"]:
        print("- No alternative causes available")

    for alternative in state["alternative_causes"]:
        print(
            f"- {alternative['cause']} "
            f"(score: {alternative['score']}, "
            f"relative share: {alternative['relative_share']}%)"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()