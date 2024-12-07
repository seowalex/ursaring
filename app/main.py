from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from . import api
from .config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    FastAPICache.init(InMemoryBackend())

    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {settings.YNAB_API_TOKEN}"},
        base_url=settings.YNAB_API_BASE_URL,
    ) as client:
        yield {"http_client": client}


app = FastAPI(openapi_url=None, lifespan=lifespan)
app.mount(settings.API_PREFIX, api.app)


@app.get(settings.API_PREFIX)
def redirect_api():
    return RedirectResponse(f"{settings.API_PREFIX}/")


app.mount("/", StaticFiles(directory="dist", html=True))
