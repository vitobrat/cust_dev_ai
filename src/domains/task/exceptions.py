"""Task domain exceptions hierarchy."""


class TaskError(Exception):
    """Base exception for task domain."""


class TaskNotFound(TaskError):
    """Raised when a requested task entity does not exist."""


class TaskCreationFailed(TaskError):
    """Raised when task creation fails due to a server-side error."""


class TaskGetFailed(TaskNotFound):
    """Raised when task retrieval fails because the entity does not exist."""


class TaskUpdateFailed(TaskNotFound):
    """Raised when task update fails because the entity does not exist."""


class TaskDeletionFailed(TaskNotFound):
    """Raised when task deletion fails because the entity does not exist."""
