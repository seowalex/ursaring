from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_users.router.oauth import generate_state_token

from . import api
from .config import settings
from .core.auth import oauth_client
from .core.db import create_db_and_tables
from .core.users import auth_backend, fastapi_users


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_db_and_tables()

    async with httpx.AsyncClient(base_url=settings.YNAB_API_BASE_URL) as client:
        yield {"http_client": client}


app = FastAPI(lifespan=lifespan)
app.include_router(
    fastapi_users.get_oauth_router(oauth_client, auth_backend, settings.SECRET_KEY),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/login")
async def login(request: Request):
    authorize_redirect_url = str(
        request.url_for(f"oauth:{oauth_client.name}.{auth_backend.name}.callback")
    )
    state = generate_state_token({}, settings.SECRET_KEY)
    authorization_url = await oauth_client.get_authorization_url(
        authorize_redirect_url, state
    )

    return RedirectResponse(authorization_url)


app.mount(settings.API_PREFIX, api.app)


@app.get(settings.API_PREFIX)
def redirect_api():
    return RedirectResponse(f"{settings.API_PREFIX}/")


app.mount("/", StaticFiles(directory="dist", html=True))
