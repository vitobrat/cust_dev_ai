"""add interview simulation task type

Revision ID: 9f13a6e2b4c8
Revises: cb6776690b76
Create Date: 2026-05-02 18:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9f13a6e2b4c8"
down_revision: Union[str, Sequence[str], None] = "cb6776690b76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TASK_TYPE_ENUM_NAME = "tasktype"
_INTERVIEW_SIMULATION_LABEL = "INTERVIEW_SIMULATION"
_PREVIOUS_TASK_TYPE_LABELS = (
    "PERSONAS_PIPELINE",
    "PERSONAS_GENERATION",
    "SINGLE_PERSONA_GENERATION",
    "SUB_INTERVIEW_GENERATION",
    "REPORT_GENERATION",
)


def upgrade() -> None:
    """Add interview simulation task type to the existing PostgreSQL enum."""
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'INTERVIEW_SIMULATION'",
        )


def downgrade() -> None:
    """Remove interview simulation task type by rebuilding the PostgreSQL enum."""
    bind = op.get_bind()
    task_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM tasks WHERE type = :task_type LIMIT 1",
        ),
        {"task_type": _INTERVIEW_SIMULATION_LABEL},
    ).first()
    if task_exists is not None:
        raise RuntimeError(
            "Cannot downgrade tasktype enum while interview simulation tasks exist.",
        )

    old_enum_name = f"{_TASK_TYPE_ENUM_NAME}_old"
    op.execute(f"ALTER TYPE {_TASK_TYPE_ENUM_NAME} RENAME TO {old_enum_name}")

    previous_task_type_enum = postgresql.ENUM(
        *_PREVIOUS_TASK_TYPE_LABELS,
        name=_TASK_TYPE_ENUM_NAME,
    )
    previous_task_type_enum.create(bind, checkfirst=False)

    op.execute(
        f"ALTER TABLE tasks ALTER COLUMN type TYPE {_TASK_TYPE_ENUM_NAME} USING type::text::{_TASK_TYPE_ENUM_NAME}",
    )
    op.execute(f"DROP TYPE {old_enum_name}")
