from agent.state import AgentState
from agent.workflow import DebuggerWorkflow
from web.schemas import DiagnosisRequest, DiagnosisResponse

workflow = DebuggerWorkflow()

def run_diagnosis(
    payload: DiagnosisRequest ,
) -> DiagnosisResponse :
    """
    convert validated web input into agentstate, run the debugger, and validate the final result.
    """
    
    initial_state: AgentState = {
        "endpoint" : payload.endpoint ,
        "method" : payload.method ,
        "status_code" : payload.status_code ,
        "error_message" : payload.error_message ,
        "stack_trace" : payload.stack_trace ,
    }
    
    result = workflow.run(initial_state)
    
    return DiagnosisResponse.model_validate(result)