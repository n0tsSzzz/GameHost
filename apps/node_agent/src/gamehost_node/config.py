from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAMEHOST_", env_file=".env", extra="ignore")

    node_agent_api_key: str = Field(default="dev-node-agent-key", min_length=8)


def get_settings() -> Settings:
    return Settings()
