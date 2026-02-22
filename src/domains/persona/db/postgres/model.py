"""Persona domain ORM model for PostgreSQL."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.postgres.base import Base
from src.infrastructure.db.postgres.base import created_at as created_date
from src.infrastructure.db.postgres.base import updated_at as updated_date
from src.infrastructure.db.postgres.base import uuidpk

if TYPE_CHECKING:
    from src.domains.interview.db.postgres.model import InterviewsOrm


class PersonasOrm(Base):
    """ORM model representing a user persona.

    A persona is a fictional character representing a segment of target users,
    with demographic information and biographical description. Personas are
    generated as part of customer development interviews.

    Attributes:
        id: Unique identifier (UUID).
        demographic_state: JSON object containing demographic characteristics
            (age, gender, location, occupation, etc.).
        bio_description: Textual biography describing the persona's background,
            motivations, and behaviors.
        is_verified: Flag indicating whether the persona has been verified/approved.
        created_at: Timestamp when the persona was created (UTC).
        updated_at: Timestamp when the persona was last updated (UTC).
        interview_id: Foreign key reference to the parent interview.
        interview: Relationship to the parent InterviewsOrm instance (eagerly loaded).
    """

    __tablename__ = "personas"

    id: Mapped[uuidpk]
    demographic_state: Mapped[dict] = mapped_column(JSONB)
    bio_description: Mapped[str]
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[created_date]
    updated_at: Mapped[updated_date]
    interview_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"),
    )

    interview: Mapped["InterviewsOrm"] = relationship(
        back_populates="personas",
        lazy="joined",
    )
