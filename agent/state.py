
from typing import Dict, Optional, TypedDict, List, Any


class AgentState(TypedDict, total=False):
    
    # input data
    status_code : Optional[str]
    error_message : str
    stack_trace : str
    
    # classsification results
    failure_type : Optional[str]
    signals : List[str]
    
    # Hyothesis result
    hypotheses: List[Dict[str, Any]]