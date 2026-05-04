"""Task domain ORM model for PostgreSQL."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domains.task.app.constants import TaskStatus, TaskType
from src.infrastructure.db.postgres.base import Base
from src.infrastructure.db.postgres.base import created_at as created_date
from src.infrastructure.db.postgres.base import updated_at as updated_date
from src.infrastructure.db.postgres.base import uuidpk

if TYPE_CHECKING:
    from src.domains.user.db.postgres.model import UsersOrm


class TasksOrm(Base):
    """ORM model representing an asynchronous background task.

    Tasks track long-running operations such as persona generation,
    full interview simulation, and final report generation. Each task has a
    type, status, progress indicator, and optional error logging.

    Attributes:
        id: Unique identifier (UUID).
        type: Type of task, for example personas_generation, interview_simulation, or report_generation.
        status: Current status of the task (created, pending, in_progress, completed, failed, etc.).
        progress: Task completion progress as a float (0.0 to 1.0).
        error_log: Optional error message or stack trace if the task failed.
        params: JSON object containing task-specific parameters and configuration.
        created_at: Timestamp when the task was created (UTC).
        updated_at: Timestamp when the task was last updated (UTC).
        user_id: Foreign key reference to the user who owns this task.
        user: Relationship to the parent UsersOrm instance (eagerly loaded).
    """

    __tablename__ = "tasks"

    id: Mapped[uuidpk]
    type: Mapped[TaskType]
    status: Mapped[TaskStatus]
    progress: Mapped[float]
    error_log: Mapped[Optional[str]]
    input_params: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[created_date]
    updated_at: Mapped[updated_date]
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    user: Mapped["UsersOrm"] = relationship(
        back_populates="tasks",
        lazy="joined",
    )
