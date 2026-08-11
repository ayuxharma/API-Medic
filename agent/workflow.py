from .classifier import FailureClassifier
from .eliminator import HypothesisEliminator
from .evidence_matcher import EvidenceMatcher
from .fixer import FixSuggester
from .hypothesis import HypothesisGenerator
from .reasoner import RootCauseReasoner
from .state import AgentState


class DebuggerWorkflow:
    """
    Coordinates the complete API debugging pipeline.
    """

    def __init__(self) -> None:
        """
        Create one instance of every pipeline component.
        """
        self.classifier = FailureClassifier()
        self.generator = HypothesisGenerator()
        self.matcher = EvidenceMatcher()
        self.eliminator = HypothesisEliminator()
        self.reasoner = RootCauseReasoner()
        self.fixer = FixSuggester()

    def run(self, initial_state: AgentState) -> AgentState:
        """
        Run every pipeline stage in the correct order.
        """
        state: AgentState = initial_state.copy()

        state = self.classifier.classify(state)
        state = self.generator.generate(state)
        state = self.matcher.match(state)
        state = self.eliminator.eliminate(state)
        state = self.reasoner.reason(state)
        state = self.fixer.suggest(state)

        return state
