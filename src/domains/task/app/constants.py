"""Task domain constants and enumerations."""

from enum import Enum


class TaskType(Enum):
    """Enumeration of available task types.

    Defines the types of asynchronous background tasks that can be executed
    in the system.

    Attributes:
        PERSONAS_GENERATION: Task for batch generation of multiple user personas.
        SINGLE_PERSONA_GENERATION: Task for generating a single user persona.
        SUB_INTERVIEW_GENERATION: Task for generating sub-interview questions and flows.
        REPORT_GENERATION: Task for generating final interview reports.
    """

    PERSONAS_GENERATION = "personas_generation"
    SINGLE_PERSONA_GENERATION = "single_persona_generation"
    SUB_INTERVIEW_GENERATION = "sub_interview_generation"
    REPORT_GENERATION = "report_generation"


class TaskStatus(Enum):
    """Enumeration of task execution statuses.

    Represents the lifecycle states of a background task from creation to completion
    or failure.

    Attributes:
        CREATED: Task has been created but not yet queued for execution.
        PENDING: Task is queued and waiting for execution.
        IN_PROGRESS: Task is currently being executed.
        COMPLETED: Task has completed successfully.
        FAILED: Task has failed with a recoverable error.
        CRITICAL_ERROR: Task has failed with a critical, non-recoverable error.
        CANCELLED: Task has been cancelled by user or system.
    """

    CREATED = "created"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CRITICAL_ERROR = "critical_error"
    CANCELLED = "cancelled"
