"""Interview domain ORM model for PostgreSQL."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.postgres.base import Base
from src.infrastructure.db.postgres.base import created_at as created_date
from src.infrastructure.db.postgres.base import updated_at as updated_date
from src.infrastructure.db.postgres.base import uuidpk

if TYPE_CHECKING:
    from src.domains.persona.db.postgres.model import PersonasOrm
    from src.domains.sub_interview.db.postgres.model import SubInterviewsOrm
    from src.domains.user.db.postgres.model import UsersOrm


class InterviewsOrm(Base):
    """ORM model representing a customer development interview.

    An interview is the main entity that aggregates personas and sub-interviews.
    It belongs to a user and may contain a generated report.

    Attributes:
        id: Unique identifier (UUID).
        report_content_url: Optional internal object URI to the generated interview report.
        created_at: Timestamp when the interview was created (UTC).
        updated_at: Timestamp when the interview was last updated (UTC).
        user_id: Foreign key reference to the user who owns this interview.
        user: Relationship to the parent UsersOrm instance (eagerly loaded).
        personas: List of PersonasOrm instances associated with this interview
            (loaded via selectin strategy).
        sub_interviews: List of SubInterviewsOrm instances associated with this interview
            (loaded via selectin strategy).
    """

    __tablename__ = "interviews"

    id: Mapped[uuidpk]
    report_content_url: Mapped[Optional[str]]
    final_report: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[created_date]
    updated_at: Mapped[updated_date]
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    user: Mapped["UsersOrm"] = relationship(
        back_populates="interviews",
        lazy="joined",
    )

    personas: Mapped[list["PersonasOrm"]] = relationship(
        back_populates="interview",
        lazy="selectin",
        passive_deletes="all",
    )

    sub_interviews: Mapped[list["SubInterviewsOrm"]] = relationship(
        back_populates="interview",
        lazy="selectin",
        passive_deletes="all",
    )
