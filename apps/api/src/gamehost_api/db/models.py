from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from gamehost_shared.enums import UserRole
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
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
