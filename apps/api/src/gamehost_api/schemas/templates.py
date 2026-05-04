from uuid import UUID

from gamehost_shared.schemas import CamelModel
from pydantic import Field


class TemplateBase(CamelModel):
    slug: str
    display_name: str
    docker_image: str
    default_env: dict[str, object] = Field(default_factory=dict)
    default_ports: list[dict[str, object]] = Field(default_factory=list)
    default_volumes: list[dict[str, object]] = Field(default_factory=list)
    min_resources: dict[str, object] = Field(default_factory=dict)
    is_public: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(CamelModel):
    display_name: str | None = None
    docker_image: str | None = None
    default_env: dict[str, object] | None = None
    default_ports: list[dict[str, object]] | None = None
    default_volumes: list[dict[str, object]] | None = None
    min_resources: dict[str, object] | None = None
    is_public: bool | None = None


class TemplateResponse(TemplateBase):
    id: UUID
