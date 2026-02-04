"""
Dependency utilities for the FastAPI application.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Callable

from dependency_injector.wiring import Provide

from src.configs.config import AppConfigs
from src.configs.constants import PROJECT_ROOT
from src.configs.log.logger import Logger
from src.infrastructure.containers.root import RootContainer

# Default configuration file used when the ``CONFIG_PATH`` environment variable
# is not set. This mirrors the previous behaviour where the path was hard‑coded.
_DEFAULT_CONFIG_PATH: Path = Path(PROJECT_ROOT, 'config', 'config.dev.yaml')


@lru_cache(maxsize=1)
def get_settings() -> AppConfigs:
    """Return cached application settings.

    The function reads the ``CONFIG_PATH`` environment variable to determine
    which YAML file to load. If the variable is absent, the default development
    configuration is used. The result is cached so subsequent calls return the
    same ``AppConfigs`` instance.
    """

    config_path_str: str | None = os.getenv('CONFIG_PATH')
    path: Path = Path(config_path_str) if config_path_str else _DEFAULT_CONFIG_PATH
    return AppConfigs.from_yaml(path)


def make_logger(
    logger_name: str,
    logger_factory: Callable[..., Logger] = Provide[RootContainer.logger],
) -> Logger:
    """Create a :class:`Logger` with the given ``logger_name``.

    The ``logger_factory`` argument defaults to the ``RootContainer.logger``
    provider, which supplies the ``logging_config_file`` from the container's
    configuration. This design allows the function to be used directly in any
    module without manually passing the configuration path.

    Args:
        logger_name: Name for the logger instance (e.g., module name).
        logger_factory: Callable that returns a :class:`Logger`. It is
            injected via ``dependency_injector`` and can be overridden in
            tests.

    Returns:
        A configured :class:`Logger` instance.
    """

    return logger_factory(logger_name=logger_name)
