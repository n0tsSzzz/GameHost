"""add node public host

Revision ID: 0006_node_public_host
Revises: 0005_backups
Create Date: 2026-05-05 03:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_node_public_host"
down_revision: str | None = "0005_backups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "nodes",
        sa.Column("public_host", sa.String(length=255), nullable=False, server_default="localhost"),
    )
    op.alter_column("nodes", "public_host", server_default=None)


def downgrade() -> None:
    op.drop_column("nodes", "public_host")
