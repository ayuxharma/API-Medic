from agent.classifier import FailureClassifier
from agent.hypothesis import HypothesisGenerator
from agent.state import AgentState
from agent.evidence_matcher import EvidenceMatcher
from agent.eliminator import HypothesisEliminator


def main():
    state: AgentState = {
        "status_code": 401,
        "error_message": "JWT token expired",
        "stack_trace": "",
    }

    classifier = FailureClassifier()
    generator = HypothesisGenerator()
    matcher = EvidenceMatcher()
    eliminator = HypothesisEliminator()

    state = classifier.classify(state)
    state = generator.generate(state)
    state = matcher.match(state)
    state = eliminator.eliminate(state)

    print("\nFailure category:", state["failure_type"])

    print("\nClassification signals:")
    for signal in state["signals"]:
        print("-", signal)

    print("\nPossible causes after evidence matching:")

    for index, hypothesis in enumerate(state["hypotheses"], start=1):
        print(
            f"{index}. {hypothesis['cause']} "
            f"(score: {hypothesis['score']})"
        )

        for evidence in hypothesis["supporting_evidence"]:
            print(f"   + {evidence}")

        for evidence in hypothesis["weakening_evidence"]:
            print(f"   - {evidence}")


if __name__ == "__main__":
    main()