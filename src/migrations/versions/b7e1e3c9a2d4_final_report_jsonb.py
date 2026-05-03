"""add final report json payload to interviews

Revision ID: b7e1e3c9a2d4
Revises: 9f13a6e2b4c8
Create Date: 2026-05-03 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7e1e3c9a2d4"
down_revision: Union[str, Sequence[str], None] = "9f13a6e2b4c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable JSONB storage for generated final interview reports."""
    op.add_column(
        "interviews",
        sa.Column(
            "final_report",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove generated final interview report storage."""
    op.drop_column("interviews", "final_report")
