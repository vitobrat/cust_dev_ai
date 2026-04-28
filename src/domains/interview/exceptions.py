"""Interview domain exceptions hierarchy."""


class InterviewError(Exception):
    """Base exception for interview domain."""


class InterviewNotFound(InterviewError):
    """Raised when a requested interview entity does not exist."""


class InterviewCreationFailed(InterviewError):
    """Raised when interview creation fails due to a server-side error."""


class InterviewGetFailed(InterviewNotFound):
    """Raised when interview retrieval fails because the entity does not exist."""


class InterviewUpdateFailed(InterviewNotFound):
    """Raised when interview update fails because the entity does not exist."""


class InterviewDeletionFailed(InterviewNotFound):
    """Raised when interview deletion fails because the entity does not exist."""


class PreInterviewPreparationDraftNodeError(InterviewError):
    """Raised when a draft pre-interview preparation graph node is executed."""


class InterviewSimulationDraftNodeError(InterviewError):
    """Raised when a draft interview simulation graph node is executed."""


class PostInterviewUpdateDraftNodeError(InterviewError):
    """Raised when a draft post-interview update graph node is executed."""


class InterviewOrchestratorDraftNodeError(InterviewError):
    """Raised when a draft interview orchestration graph node is executed."""
