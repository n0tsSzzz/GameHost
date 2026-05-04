from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from gamehost_shared.enums import (
    NodeStatus,
    ServerMemberRole,
    ServerStatus,
    TaskKind,
    TaskStatus,
    UserRole,
)
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from gamehost_api.db.base import Base

UuidPk = Annotated[UUID, mapped_column(primary_key=True, default=uuid7)]
CreatedAt = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC)),
]


class User(Base):
    __tablename__ = "users"

    id: Mapped[UuidPk]
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda item: [role.value for role in item],
        ),
        default=UserRole.USER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[CreatedAt]

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),)

    id: Mapped[UuidPk]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    ip: Mapped[str | None] = mapped_column(String(64), default=None)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[UuidPk]
    name: Mapped[str] = mapped_column(String(120), unique=True)
    endpoint_url: Mapped[str] = mapped_column(String(2048))
    api_key_hash: Mapped[str] = mapped_column(Text)
    capacity_cpu: Mapped[int] = mapped_column(Integer)
    capacity_mem_mb: Mapped[int] = mapped_column(Integer)
    status: Mapped[NodeStatus] = mapped_column(
        SqlEnum(
            NodeStatus,
            name="node_status",
            values_callable=lambda item: [status.value for status in item],
        ),
        default=NodeStatus.OFFLINE,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class GameTemplate(Base):
    __tablename__ = "game_templates"

    id: Mapped[UuidPk]
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(180))
    docker_image: Mapped[str] = mapped_column(String(300))
    default_env: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    default_ports: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    default_volumes: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    min_resources: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[UuidPk]
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    template_id: Mapped[UUID] = mapped_column(ForeignKey("game_templates.id"))
    node_id: Mapped[UUID | None] = mapped_column(ForeignKey("nodes.id"), default=None)
    container_id: Mapped[str | None] = mapped_column(String(128), default=None)
    status: Mapped[ServerStatus] = mapped_column(
        SqlEnum(
            ServerStatus,
            name="server_status",
            values_callable=lambda item: [status.value for status in item],
        ),
        default=ServerStatus.PENDING,
    )
    host: Mapped[str | None] = mapped_column(String(255), default=None)
    port: Mapped[int | None] = mapped_column(Integer, default=None)
    env_overrides: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    resources: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    owner: Mapped[User] = relationship()
    template: Mapped[GameTemplate] = relationship()
    node: Mapped[Node | None] = relationship()


class ServerMember(Base):
    __tablename__ = "server_members"

    server_id: Mapped[UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[ServerMemberRole] = mapped_column(
        SqlEnum(
            ServerMemberRole,
            name="server_member_role",
            values_callable=lambda item: [role.value for role in item],
        ),
    )
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[CreatedAt]


class ServerInvite(Base):
    __tablename__ = "server_invites"

    id: Mapped[UuidPk]
    server_id: Mapped[UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[ServerMemberRole] = mapped_column(
        SqlEnum(
            ServerMemberRole,
            name="server_member_role",
            values_callable=lambda item: [role.value for role in item],
        ),
    )
    token: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[CreatedAt]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UuidPk]
    server_id: Mapped[UUID | None] = mapped_column(ForeignKey("servers.id", ondelete="SET NULL"))
    kind: Mapped[TaskKind] = mapped_column(
        SqlEnum(
            TaskKind,
            name="task_kind",
            values_callable=lambda item: [kind.value for kind in item],
        ),
    )
    status: Mapped[TaskStatus] = mapped_column(
        SqlEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda item: [status.value for status in item],
        ),
        default=TaskStatus.QUEUED,
    )
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UuidPk]
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(120), index=True)
    target_type: Mapped[str] = mapped_column(String(80), index=True)
    target_id: Mapped[str] = mapped_column(String(120), index=True)
    meta: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[CreatedAt]
