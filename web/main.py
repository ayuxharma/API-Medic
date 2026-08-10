from fastapi import FastAPI

from agent.state import AgentState
from agent.workflow import DebuggerWorkflow
from web.schemas import DiagnosisRequest, DiagnosisResponse


app = FastAPI(
    title="API Failure Debugger",
    description=(
        "A rule-based application that analyzes API failures, "
        "ranks possible root causes, and suggests fixes."
    ),
    version="0.1.0",
)

workflow = DebuggerWorkflow()


@app.get("/")
def home() -> dict[str, str]:
    """
    Return basic information about the application.

    This route will later be replaced by the HTML debugging form.
    """
    return {
        "message": "API Failure Debugger is running",
        "documentation": "/docs",
        "health_check": "/health",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Confirm that the web application is running.
    """
    return {
        "status": "healthy",
    }



@app.post(
    "/api/diagnose",
    response_model=DiagnosisResponse,
)
def diagnose_api_failure(
    payload: DiagnosisRequest,
) -> DiagnosisResponse:
    """
    Analyze an API failure and return the debugging result.
    """

    initial_state: AgentState = {
        "endpoint": payload.endpoint,
        "method": payload.method,
        "status_code": payload.status_code,
        "error_message": payload.error_message,
        "stack_trace": payload.stack_trace,
    }

    result = workflow.run(initial_state)

    return DiagnosisResponse.model_validate(result)