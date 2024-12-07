from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.utils import is_body_allowed_for_status_code

from ..config import settings
from .routes import transactions

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url="/",
    redoc_url=None,
)


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException):
    headers = getattr(exc, "headers", None)

    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)

    return JSONResponse(
        {"error": exc.detail}, status_code=exc.status_code, headers=headers
    )


app.include_router(transactions.router, prefix="/transactions")
