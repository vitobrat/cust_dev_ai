"""Sub-interview domain ORM model for PostgreSQL."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.infrastructure.db.postgres.base import Base
from src.infrastructure.db.postgres.base import created_at as created_date
from src.infrastructure.db.postgres.base import uuidpk

if TYPE_CHECKING:
    from src.domains.interview.db.postgres.model import InterviewsOrm


class SubInterviewsOrm(Base):
    """ORM model representing a sub-interview session.

    A sub-interview is a conversational session within a larger interview,
    typically focused on a specific persona or topic. It maintains a chat
    history and tracks its execution status.

    Attributes:
        id: Unique identifier (UUID).
        chat_history: JSON object containing the conversation history
            (messages, timestamps, metadata).
        status: Current status of the sub-interview (pending, initializing,
            generating, saving, completed, failed).
        created_at: Timestamp when the sub-interview was created (UTC).
        interview_id: Foreign key reference to the parent interview.
        interview: Relationship to the parent InterviewsOrm instance (eagerly loaded).
    """

    __tablename__ = "sub_interviews"

    id: Mapped[uuidpk]
    chat_history: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[SubInterviewStatus]
    created_at: Mapped[created_date]
    interview_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"),
    )

    interview: Mapped["InterviewsOrm"] = relationship(
        back_populates="sub_interviews",
        lazy="joined",
    )
