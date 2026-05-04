from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAMEHOST_", env_file=".env", extra="ignore")

    env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://gamehost:gamehost@localhost:5432/gamehost"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="dev-only-change-me", min_length=16)
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    refresh_cookie_name: str = "refresh_token"
    frontend_origin: str = "https://gamehost.localhost"


def get_settings() -> Settings:
    return Settings()
