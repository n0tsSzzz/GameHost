from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAMEHOST_", env_file=".env", extra="ignore")

    env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    domain: str = "localhost"
    database_url: str = "postgresql+asyncpg://gamehost:gamehost@localhost:5432/gamehost"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="dev-only-change-me", min_length=16)
    node_agent_api_key: str = "dev-node-agent-key"
    node_agent_timeout_seconds: float = 300.0
    admin_email: str | None = None
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = False
    frontend_origin: str = "http://localhost:3000"
    log_tail_limit: int = 500


def get_settings() -> Settings:
    return Settings()
