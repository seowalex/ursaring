from typing import Any

from fastapi import HTTPException
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
                        headers={"Authorization": f"Besarer {token}"},
                    )
                ).raise_for_status()
            except HTTPStatusError as e:
                error = ErrorResponse.model_validate_json(e.response.text).error

                raise HTTPException(e.response.status_code, detail=error.model_dump())

        user = UserResponse.model_validate_json(response.text).data.user

        return str(user.id), f"{user.id}@ynab.com"


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=CookieTransport(cookie_samesite="strict"),
    get_strategy=lambda: JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=None),
)
