"""Base SQLAlchemy models and type annotations for PostgreSQL."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column

uuidpk = Annotated[
    uuid.UUID,
    mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
]
"""Type annotation for UUID primary key with automatic generation.

Uses PostgreSQL's gen_random_uuid() function to generate UUIDs on the database side.
"""

created_at = Annotated[
    datetime,
    mapped_column(server_default=text("TIMEZONE('utc', now())")),
]
"""Type annotation for creation timestamp with automatic UTC timezone."""

updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=lambda: datetime.now(timezone.utc),
    ),
]
"""Type annotation for update timestamp with automatic UTC timezone.

Automatically updates on each record modification.
"""


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Provides customizable __repr__ implementation that avoids loading relationships
    to prevent unexpected database queries (N+1 problem).

    Attributes:
        repr_cols_num: Number of columns to include in repr by default. Defaults to 3.
        repr_cols: Tuple of specific column names to always include in repr.
    """

    repr_cols_num: int = 3
    repr_cols: tuple[str, ...] = tuple()

    def __repr__(self) -> str:
        """Generate string representation of the model instance.

        Only includes table columns (not relationships) to avoid lazy loading.
        Includes first `repr_cols_num` columns and any columns specified in `repr_cols`.

        Returns:
            String representation in format: <ClassName col1=val1, col2=val2, ...>
        """
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"
