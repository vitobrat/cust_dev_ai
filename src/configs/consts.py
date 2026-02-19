import os
import types
from pathlib import Path

_DEFAULT_PROJECT_PATH = Path(__file__).resolve().parent.parent.parent

_DEFAULT_CONFIG_PATH = Path(_DEFAULT_PROJECT_PATH, "config", "config.dev.yaml")

DEFAULT_GRAPH_RECURSION_LIMIT = 1

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", _DEFAULT_PROJECT_PATH))

valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

INSTRUCTOR_ROLE_MAP = types.MappingProxyType(
    {
        "human": "user",
        "ai": "assistant",
        "system": "system",
    },
)
