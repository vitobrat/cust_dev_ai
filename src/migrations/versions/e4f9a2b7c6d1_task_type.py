"""backfill task input params discriminator

Revision ID: e4f9a2b7c6d1
Revises: b7e1e3c9a2d4
Create Date: 2026-05-04 19:15:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f9a2b7c6d1"
down_revision: Union[str, Sequence[str], None] = "b7e1e3c9a2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill the Pydantic discriminator for legacy task payloads."""
    op.execute(
        """
        UPDATE tasks
        SET input_params = jsonb_set(
            input_params,
            '{task_type}',
            to_jsonb(
                (
                    CASE type::text
                        WHEN 'PERSONAS_PIPELINE' THEN 'personas_pipeline'
                        WHEN 'PERSONAS_GENERATION' THEN 'personas_generation'
                        WHEN 'SINGLE_PERSONA_GENERATION' THEN 'single_persona_generation'
                        WHEN 'INTERVIEW_SIMULATION' THEN 'interview_simulation'
                        WHEN 'SUB_INTERVIEW_GENERATION' THEN 'sub_interview_generation'
                        WHEN 'REPORT_GENERATION' THEN 'report_generation'
                    END
                )::text
            ),
            true
        )
        WHERE NOT input_params ? 'task_type';
        """,
    )


def downgrade() -> None:
    """Remove the discriminator added to legacy task payloads."""
    op.execute(
        """
        UPDATE tasks
        SET input_params = input_params - 'task_type'
        WHERE input_params ? 'task_type';
        """,
    )
