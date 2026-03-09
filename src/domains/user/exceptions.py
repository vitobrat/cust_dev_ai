"""User domain exceptions hierarchy."""


class UserError(Exception):
    """Base exception for user domain."""


class UserNotFound(UserError):
    """Raised when a requested user entity does not exist."""


class UserCreationFailed(UserError):
    """Raised when user creation fails due to a server-side error."""


class UserGetFailed(UserNotFound):
    """Raised when user retrieval fails because the entity does not exist."""


class UserUpdateFailed(UserNotFound):
    """Raised when user update fails because the entity does not exist."""


class UserDeletionFailed(UserNotFound):
    """Raised when user deletion fails because the entity does not exist."""
