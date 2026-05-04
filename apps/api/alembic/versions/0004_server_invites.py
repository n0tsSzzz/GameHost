"""create server invites

Revision ID: 0004_server_invites
Revises: 0003_servers_tasks_audit
Create Date: 2026-05-05 01:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_server_invites"
down_revision: str | None = "0003_servers_tasks_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "server_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.Enum("viewer", "operator", name="server_member_role"), nullable=False),
        sa.Column("token", sa.String(length=160), nullable=False),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_server_invites_email"), "server_invites", ["email"])
    op.create_index(op.f("ix_server_invites_server_id"), "server_invites", ["server_id"])
    op.create_index(op.f("ix_server_invites_token"), "server_invites", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_server_invites_token"), table_name="server_invites")
    op.drop_index(op.f("ix_server_invites_server_id"), table_name="server_invites")
    op.drop_index(op.f("ix_server_invites_email"), table_name="server_invites")
    op.drop_table("server_invites")
