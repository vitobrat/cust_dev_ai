"""Persona domain exceptions hierarchy."""


class PersonaError(Exception):
    """Base exception for persona domain."""


class PersonaNotFound(PersonaError):
    """Raised when a requested persona entity does not exist."""


class PersonaCreationFailed(PersonaError):
    """Raised when persona creation fails due to a server-side error."""


class PersonaGetFailed(PersonaNotFound):
    """Raised when persona retrieval fails because the entity does not exist."""


class PersonaUpdationFailed(PersonaNotFound):
    """Raised when persona update fails because the entity does not exist."""


class PersonaDeletionFailed(PersonaNotFound):
    """Raised when persona deletion fails because the entity does not exist."""
