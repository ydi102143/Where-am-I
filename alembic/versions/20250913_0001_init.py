from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "20250913_0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("why", sa.Text, nullable=False, server_default=""),
        sa.Column("kgi", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column("area", sa.String(length=50), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("(datetime('now'))")),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])
    op.create_index("ix_goals_title", "goals", ["title"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("goal_id", sa.Integer, sa.ForeignKey("goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("impact", sa.Integer, nullable=False, server_default="1"),
        sa.Column("effort_min", sa.Integer, nullable=False, server_default="30"),
        sa.Column("due", sa.Date, nullable=True),
        sa.Column("parent_task_id", sa.Integer, nullable=True),
    )
    op.create_index("ix_tasks_goal_id", "tasks", ["goal_id"])

    op.create_table(
        "reflections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("text", sa.Text, nullable=False, server_default=""),
        sa.Column("mood", sa.Integer, nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("(datetime('now'))")),
    )
    op.create_index("ix_reflections_user_id", "reflections", ["user_id"])

    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("content_json", sa.Text, nullable=False),
    )
    op.create_index("ix_suggestions_user_id", "suggestions", ["user_id"])

    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False, server_default="default"),
        sa.Column("value", sa.Text, nullable=False),
    )
    op.create_index("ix_integrations_user_id", "integrations", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_integrations_user_id", table_name="integrations")
    op.drop_table("integrations")
    op.drop_index("ix_suggestions_user_id", table_name="suggestions")
    op.drop_table("suggestions")
    op.drop_index("ix_reflections_user_id", table_name="reflections")
    op.drop_table("reflections")
    op.drop_index("ix_tasks_goal_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_goals_title", table_name="goals")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
