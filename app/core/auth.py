from typing import Any

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from httpx import HTTPStatusError
from httpx_oauth.oauth2 import BaseOAuth2

from ..config import settings
from ..models import ErrorResponse, UserResponse


class YNABOAuth2(BaseOAuth2[dict[str, Any]]):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: list[str] | None = settings.YNAB_OAUTH_BASE_SCOPES,
        name: str = "ynab",
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint=settings.YNAB_OAUTH_AUTHORIZATION_ENDPOINT,
            access_token_endpoint=settings.YNAB_OAUTH_TOKEN_ENDPOINT,
            refresh_token_endpoint=settings.YNAB_OAUTH_TOKEN_ENDPOINT,
            name=name,
            base_scopes=scopes,
        )

    async def get_id_email(self, token: str):
        async with self.get_httpx_client() as client:
            try:
                response = (
                    await client.get(
                        settings.YNAB_API_USER_ENDPOINT,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                ).raise_for_status()
            except HTTPStatusError as e:
                error = ErrorResponse.model_validate_json(e.response.text).error

                raise HTTPException(e.response.status_code, detail=error.model_dump())

        user = UserResponse.model_validate_json(response.text).data.user

        return str(user.id), f"{user.id}@ynab.com"


class CookieRedirectTransport(CookieTransport):
    async def get_login_response(self, token: str):
        return self._set_login_cookie(RedirectResponse("/"), token)


oauth_client = YNABOAuth2(
    settings.YNAB_OAUTH_CLIENT_ID, settings.YNAB_OAUTH_CLIENT_SECRET
)
auth_backend = AuthenticationBackend(
    "jwt",
    transport=CookieRedirectTransport(cookie_samesite="strict"),
    get_strategy=lambda: JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=None),
)
