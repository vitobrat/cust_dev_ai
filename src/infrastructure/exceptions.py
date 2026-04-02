"""Infrastructure-level exception classes."""


class GraphError(Exception):
    """Base exception for graph-related errors."""


class RedisRepositoryError(Exception):
    """Base exception for Redis repository errors."""
