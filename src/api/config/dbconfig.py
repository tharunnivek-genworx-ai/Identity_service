"""Environment-backed configuration for the auth backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Database and JWT settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "*"


settings = Settings()
