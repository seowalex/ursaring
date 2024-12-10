from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "Ursaring"
    PROJECT_VERSION: str = "2024.12.0"

    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite+aiosqlite:///db.sqlite3"

    YNAB_API_BASE_URL: str = "https://api.ynab.com/v1"
    YNAB_API_USER_ENDPOINT: str = f"{YNAB_API_BASE_URL}/user"

    YNAB_OAUTH_AUTHORIZATION_ENDPOINT: str = "https://app.ynab.com/oauth/authorize"
    YNAB_OAUTH_TOKEN_ENDPOINT: str = "https://app.ynab.com/oauth/token"

    YNAB_OAUTH_BASE_SCOPES: list[str] = ["read-only"]

    SECRET_KEY: str

    YNAB_OAUTH_CLIENT_ID: str
    YNAB_OAUTH_CLIENT_SECRET: str


settings = Settings()  # type: ignore
