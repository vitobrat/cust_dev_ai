"""User domain ORM model for PostgreSQL."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from src.infrastructure.db.postgres.base import Base, uuidpk

if TYPE_CHECKING:
    from src.domains.interview.db.postgres.model import InterviewsOrm
    from src.domains.task.db.postgres.model import TasksOrm


class UsersOrm(Base):
    """ORM model representing a system user.

    A user is the root entity that owns interviews and tasks.
    Relationships use lazy='raise' to prevent accidental N+1 queries
    and enforce explicit loading strategies.

    Attributes:
        id: Unique identifier (UUID).
        interviews: List of InterviewsOrm instances owned by this user.
            Must be explicitly loaded (lazy='raise').
        tasks: List of TasksOrm instances owned by this user.
            Must be explicitly loaded (lazy='raise').
    """

    __tablename__ = "users"

    id: Mapped[uuidpk]

    interviews: Mapped[list["InterviewsOrm"]] = relationship(
        back_populates="user",
        lazy="raise",
    )

    tasks: Mapped[list["TasksOrm"]] = relationship(
        back_populates="user",
        lazy="raise",
    )
