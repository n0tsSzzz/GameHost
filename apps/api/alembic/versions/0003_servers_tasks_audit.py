"""create servers tasks and audit log

Revision ID: 0003_servers_tasks_audit
Revises: 0002_templates_nodes
Create Date: 2026-05-05 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_servers_tasks_audit"
down_revision: str | None = "0002_templates_nodes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    server_status = postgresql.ENUM(
        "pending",
        "provisioning",
        "running",
        "stopped",
        "failed",
        "deleting",
        name="server_status",
        create_type=False,
    )
    server_member_role = postgresql.ENUM(
        "viewer",
        "operator",
        name="server_member_role",
        create_type=False,
    )
    task_kind = postgresql.ENUM(
        "provision_server",
        "start_server",
        "stop_server",
        "restart_server",
        "delete_server",
        name="task_kind",
        create_type=False,
    )
    task_status = postgresql.ENUM(
        "queued",
        "running",
        "succeeded",
        "failed",
        name="task_status",
        create_type=False,
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE server_status AS ENUM
            ('pending', 'provisioning', 'running', 'stopped', 'failed', 'deleting');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE server_member_role AS ENUM ('viewer', 'operator');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE task_kind AS ENUM
            ('provision_server', 'start_server', 'stop_server', 'restart_server', 'delete_server');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE TYPE task_status AS ENUM ('queued', 'running', 'succeeded', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "servers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.Uuid(), nullable=True),
        sa.Column("container_id", sa.String(length=128), nullable=True),
        sa.Column("status", server_status, nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("env_overrides", sa.JSON(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["game_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_servers_owner_id"), "servers", ["owner_id"])

    op.create_table(
        "server_members",
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", server_member_role, nullable=False),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("server_id", "user_id"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("server_id", sa.Uuid(), nullable=True),
        sa.Column("kind", task_kind, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=120), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"])
    op.create_index(op.f("ix_audit_log_target_id"), "audit_log", ["target_id"])
    op.create_index(op.f("ix_audit_log_target_type"), "audit_log", ["target_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_target_type"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_target_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("tasks")
    op.drop_table("server_members")
    op.drop_index(op.f("ix_servers_owner_id"), table_name="servers")
    op.drop_table("servers")
    for enum_name in ["task_status", "task_kind", "server_member_role", "server_status"]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
