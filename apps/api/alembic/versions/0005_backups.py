"""create backups

Revision ID: 0005_backups
Revises: 0004_server_invites
Create Date: 2026-05-05 01:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_backups"
down_revision: str | None = "0004_server_invites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE task_kind ADD VALUE IF NOT EXISTS 'backup_server'")
    op.execute("ALTER TYPE task_kind ADD VALUE IF NOT EXISTS 'restore_backup'")
    backup_status = sa.Enum("pending", "running", "succeeded", "failed", name="backup_status")
    backup_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "backups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", backup_status, nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backups_server_id"), "backups", ["server_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_backups_server_id"), table_name="backups")
    op.drop_table("backups")
    sa.Enum(name="backup_status").drop(op.get_bind(), checkfirst=True)
