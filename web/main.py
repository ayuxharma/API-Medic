from pathlib import Path
from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    Form,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from agent.input_parser import FileInputParser
from web.schemas import DiagnosisRequest, DiagnosisResponse
from web.services import run_diagnosis

BASE_DIRECTORY = Path(__file__).resolve().parent.parent
TEMPLATES_DIRECTORY = BASE_DIRECTORY / "templates"

MAX_UPLOAD_SIZE = 100_000

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIRECTORY),
)

file_parser = FileInputParser()


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
    Display the browser-based debugging form.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": None,
        },
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
    Accept JSON data and return a JSON diagnosis.
    """
    return run_diagnosis(payload)


@app.post("/diagnose", response_class=HTMLResponse)
def diagnose_from_form(
    request: Request,
    payload: Annotated[DiagnosisRequest, Form()],
) -> HTMLResponse:
    """
    Accept manually entered form data and display the result.
    """

    result = run_diagnosis(payload)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": result,
        },
    )


@app.post(
    "/diagnose/upload",
    response_class=HTMLResponse,
)
async def diagnose_from_uploaded_file(
    request: Request,
    file: Annotated[
        UploadFile,
        File(description="Structured API error text file"),
    ],
) -> HTMLResponse:
    """
    Parse an uploaded UTF-8 text file and display its diagnosis.
    """

    try:
        uploaded_content = await file.read(MAX_UPLOAD_SIZE + 1)
    finally:
        await file.close()

    if len(uploaded_content) > MAX_UPLOAD_SIZE:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": "Uploaded file must be 100 KB or smaller.",
            },
            status_code=413,
        )

    try:
        text_content = uploaded_content.decode("utf-8")

        parsed_state = file_parser.parse_text(text_content)

        payload = DiagnosisRequest.model_validate(parsed_state)

        result = run_diagnosis(payload)

    except UnicodeDecodeError:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": ("Uploaded file must contain valid UTF-8 text."),
            },
            status_code=400,
        )

    except (ValueError, ValidationError) as error:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(error),
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": result,
        },
    )
