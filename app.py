from agent.classifier import FailureClassifier
from agent.hypothesis import HypothesisGenerator
from agent.state import AgentState


def main():
    state: AgentState = {
        "status_code": 401,
        "error_message": "JWT token expired",
        "stack_trace": "",
    }

    classifier = FailureClassifier()
    generator = HypothesisGenerator()

    state = classifier.classify(state)
    state = generator.generate(state)

    print("\nFailure category:", state["failure_type"])

    print("\nClassification signals:")
    for signal in state["signals"]:
        print("-", signal)

    print("\nPossible causes:")
    for index, hypothesis in enumerate(state["hypotheses"], start=1):
        print(
            f"{index}. {hypothesis['cause']} "
            f"(starting score: {hypothesis['score']})"
        )


if __name__ == "__main__":
    main()