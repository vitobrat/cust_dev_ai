"""Sub-interview domain exceptions hierarchy."""


class SubInterviewError(Exception):
    """Base exception for sub-interview domain."""


class SubInterviewNotFound(SubInterviewError):
    """Raised when a requested sub-interview entity does not exist."""


class SubInterviewCreationFailed(SubInterviewError):
    """Raised when sub-interview creation fails due to a server-side error."""


class SubInterviewGetFailed(SubInterviewNotFound):
    """Raised when sub-interview retrieval fails because the entity does not exist."""


class SubInterviewUpdateFailed(SubInterviewNotFound):
    """Raised when sub-interview update fails because the entity does not exist."""


class SubInterviewDeletionFailed(SubInterviewNotFound):
    """Raised when sub-interview deletion fails because the entity does not exist."""
