from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from web.schemas import DiagnosisRequest, DiagnosisResponse
from web.services import run_diagnosis


BASE_DIRECTORY = Path(__file__).resolve().parent.parent
TEMPLATES_DIRECTORY = BASE_DIRECTORY / "templates"

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIRECTORY),
)


app = FastAPI(
    title="API Failure Debugger",
    description=(
        "A rule-based application that analyzes API failures, "
        "ranks possible root causes, and suggests fixes."
    ),
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """
    Display the browser-based API debugging form.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


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
    Accept JSON input and return a JSON diagnosis.
    """
    return run_diagnosis(payload)


@app.post("/diagnose", response_class=HTMLResponse)
def diagnose_from_form(
    request: Request,
    payload: Annotated[DiagnosisRequest, Form()],
) -> HTMLResponse:
    """
    Accept browser form input and display an HTML diagnosis.
    """

    result = run_diagnosis(payload)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": result,
        },
    )