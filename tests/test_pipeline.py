from agent.workflow import DebuggerWorkflow
from agent.state import AgentState

def run_pipeline(state: AgentState) -> AgentState:
    workflow = DebuggerWorkflow()
    return workflow.run(state)

def create_state(status_code, error_message, stack_trace="") -> AgentState :
    return {
        "endpoint" : "/api/test" ,
        "method" : "POST" ,
        "status_code" : status_code ,
        "error_message" : error_message ,
        "stack_trace" : stack_trace ,
    }
    
def test_expired_jwt_pipeline() :
    state = create_state(401, "JWT token expired")
    result = run_pipeline(state) 
    
    assert result["failure_type"] == "AUTHENTICATION"
    assert result["root_cause"] == "JWT token has expired"
    assert result["confidence_score"] >= 0.8
    assert len(result["suggested_fixes"]) > 0
    
    primary = result["hypotheses"][0]
    
    assert primary["cause"] == "JWT token has expired"
    assert len(primary["supporting_evidence"]) > 0
    

def test_missing_field_pipeline() :
    state = create_state(
        400 , 
        "Required field is missing" ,
    )
    
    result = run_pipeline(state) 
    
    assert result["failure_type"] == "VALIDATION"
    assert result["root_cause"] == (
        "Required field is missing from request"
    )
    assert len(result["suggested_fixes"]) > 0


def test_undefined_variable_pipeline():
    state = create_state(
        500,
        "Undefined variable user_id",
        "user_id is not defined",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "SERVER_ERROR"
    assert result["root_cause"] == (
        "Undefined variable or method call"
    )


def test_unknown_error_pipeline():
    state = create_state(
        None,
        "Something unusual happened",
    )

    result = run_pipeline(state)

    assert result["failure_type"] == "UNKNOWN"
    assert result["root_cause"] == (
        "Insufficient information to identify the root cause"
    )
    assert len(result["suggested_fixes"]) > 0