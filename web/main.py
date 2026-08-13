import logging
from pathlib import Path
from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    Form,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.base import (
    RequestResponseEndpoint,
)

from agent.input_parser import FileInputParser
from agent.logging_config import configure_logging
from web.schemas import (
    DiagnosisRequest,
    DiagnosisResponse,
)
from web.services import run_diagnosis

configure_logging()

logger = logging.getLogger(__name__)

BASE_DIRECTORY = Path(__file__).resolve().parent.parent
TEMPLATES_DIRECTORY = BASE_DIRECTORY / "templates"
STATIC_DIRECTORY = BASE_DIRECTORY / "static"

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

# Make CSS files available through /static.
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIRECTORY)),
    name="static",
)


@app.middleware("http")
async def handle_unexpected_errors(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Convert unexpected exceptions into a safe HTTP response.

    Expected validation errors are still handled normally by
    FastAPI and the individual routes.
    """

    try:
        return await call_next(request)
    except Exception as error:
        # Log safe metadata without exposing the exception message.
        logger.error(
            "event=unhandled_web_error method=%s path=%s error_type=%s",
            request.method,
            request.url.path,
            type(error).__name__,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": ("An unexpected internal error occurred."),
            },
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


@app.post(
    "/diagnose",
    response_class=HTMLResponse,
)
def diagnose_from_form(
    request: Request,
    payload: Annotated[
        DiagnosisRequest,
        Form(),
    ],
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
        File(description=("Structured API error text file")),
    ],
) -> HTMLResponse:
    """
    Parse an uploaded UTF-8 file and display its diagnosis.
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
                "error": ("Uploaded file must be 100 KB or smaller."),
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

    except (
        ValueError,
        ValidationError,
    ) as error:
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
