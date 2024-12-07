from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_PREFIX: str = "/api/v1"

    PROJECT_NAME: str = "Ursaring"
    PROJECT_VERSION: str = "2024.12.0"

    YNAB_API_BASE_URL: str = "https://api.ynab.com/v1"
    YNAB_API_TOKEN: str


settings = Settings()  # type: ignore
