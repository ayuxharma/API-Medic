from typing import Any, Dict, List

from .state import AgentState

class RootCauseReasoner :
    """
    Selects the strongest remaining hypothesis as the root cause.
    """
    
    def reason(self, state: AgentState) -> AgentState :
        """
        Rank existing hypotheses and select the strongest one.
        """
        
        hypotheses : List[Dict[str, Any]] = state.get(
            "hypotheses" , 
            []
        )
        
        # sort existing ones, do not generate them again
        hypotheses.sort(
            key=lambda hypothesis: hypothesis.get("score") ,
            reverse=True,
        )
        
        state["hypotheses"] = hypotheses
        
        # if no hypotheses exist
        if not hypotheses :
            state["root_cause"] = "Insufficient information to identify the root cause"
            state["confidence_level"] = 0.0
            state["alternative_causes"] = []
            return state
        
        primary = hypotheses[0]
        
        state["root_cause"] = primary.get("cause")
        state["confidence_level"] = primary.get("score")
        
        # calclate each remaining hypothesis's share of all scores.
        total_score = sum (
            hypothesis["score"]
            for hypothesis in hypotheses
        )
        
        alternatives = [] 
        
        for hypothesis in hypotheses[1:4] :
            relative_share = 0.0
            
            if total_score > 0 :
                relative_share = round(
                    (hypothesis["score"] / total_score) * 100,
                    1,
                )

            alternatives.append(
                {
                    "cause": hypothesis["cause"],
                    "score": hypothesis["score"],
                    "relative_share": relative_share,
                }
            )

        state["alternative_causes"] = alternatives

        return state
    