"""empty message

Revision ID: 0ffc0e239d63
Revises:
Create Date: 2026-02-23 11:36:43.747244

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0ffc0e239d63"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

task_type_enum = sa.Enum(
    "PERSONAS_PIPELINE",
    "PERSONAS_GENERATION",
    "SINGLE_PERSONA_GENERATION",
    "SUB_INTERVIEW_GENERATION",
    "REPORT_GENERATION",
    name="tasktype",
)
task_status_enum = sa.Enum(
    "CREATED",
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    "CRITICAL_ERROR",
    "CANCELLED",
    name="taskstatus",
)
sub_interview_status_enum = sa.Enum(
    "PENDING",
    "INITIALIZING",
    "GENERATING",
    "SAVING",
    "COMPLETED",
    "FAILED",
    name="subinterviewstatus",
)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "interviews",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("report_content_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("type", task_type_enum, nullable=False),
        sa.Column("status", task_status_enum, nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("error_log", sa.String(), nullable=True),
        sa.Column("input_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "personas",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("demographic_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("bio_description", sa.String(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("interview_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sub_interviews",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("chat_history", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sub_interview_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
        sa.Column("interview_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sub_interviews")
    op.drop_table("personas")
    op.drop_table("tasks")
    op.drop_table("interviews")
    op.drop_table("users")

    task_type_enum.drop(op.get_bind())
    task_status_enum.drop(op.get_bind())
    sub_interview_status_enum.drop(op.get_bind())
