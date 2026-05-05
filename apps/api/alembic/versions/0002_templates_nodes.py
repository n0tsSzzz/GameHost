"""create templates and nodes

Revision ID: 0002_templates_nodes
Revises: 0001_users_refresh_tokens
Create Date: 2026-05-04 21:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_templates_nodes"
down_revision: str | None = "0001_users_refresh_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    node_status = postgresql.ENUM(
        "online",
        "offline",
        "drain",
        name="node_status",
        create_type=False,
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE node_status AS ENUM ('online', 'offline', 'drain');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("endpoint_url", sa.String(length=2048), nullable=False),
        sa.Column("api_key_hash", sa.Text(), nullable=False),
        sa.Column("capacity_cpu", sa.Integer(), nullable=False),
        sa.Column("capacity_mem_mb", sa.Integer(), nullable=False),
        sa.Column("status", node_status, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "game_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("docker_image", sa.String(length=300), nullable=False),
        sa.Column("default_env", sa.JSON(), nullable=False),
        sa.Column("default_ports", sa.JSON(), nullable=False),
        sa.Column("default_volumes", sa.JSON(), nullable=False),
        sa.Column("min_resources", sa.JSON(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_game_templates_slug"), "game_templates", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_game_templates_slug"), table_name="game_templates")
    op.drop_table("game_templates")
    op.drop_table("nodes")
    sa.Enum(name="node_status").drop(op.get_bind(), checkfirst=True)
