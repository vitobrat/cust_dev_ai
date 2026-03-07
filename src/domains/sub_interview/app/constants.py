"""Sub-interview domain constants and enumerations."""

from enum import Enum


class SubInterviewStatus(Enum):
    """Enumeration of sub-interview execution statuses.

    Represents the lifecycle states of a sub-interview session from initialization
    to completion or failure.

    Attributes:
        PENDING: Sub-interview is created and waiting to be initialized.
        INITIALIZING: Sub-interview is being set up (loading context, preparing prompts).
        GENERATING: Sub-interview conversation is being generated (AI interaction phase).
        SAVING: Sub-interview results are being persisted to the database.
        COMPLETED: Sub-interview has completed successfully.
        FAILED: Sub-interview has failed due to an error.
    """

    PENDING = "pending"
    INITIALIZING = "initializing"
    GENERATING = "generating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
