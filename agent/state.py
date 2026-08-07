
from typing import Dict, Optional, TypedDict, List, Any


class AgentState(TypedDict, total=False):
    
    # input data
    status_code : Optional[str]
    error_message : str
    stack_trace : str
    endpoint : str
    method : str
    
    # classsification results
    failure_type : Optional[str]
    signals : List[str]
    
    # Hyothesis result
    hypotheses: List[Dict[str, Any]]
    
    # final reasoning result
    root_cause: str
    confidence_level: float
    alternative_causes: List[Dict[str, Any]]
    
    suggested_fixes: List[str]