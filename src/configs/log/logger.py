import logging
import os
from logging.config import dictConfig
from pathlib import Path
from typing import Optional

import yaml


def setup_logger(logging_config_file: Path) -> None:
    """Setup logging configuration from a YAML file specified in settings."""
    if not os.path.exists(logging_config_file):
        logging.error(
            f'Unable to configure logging. {logging_config_file} not found',
        )
        return
    with open(logging_config_file, 'r') as cfg_file:
        config = yaml.safe_load(cfg_file.read())
        dictConfig(config)


class Logger:
    """Logger wrapper class to provide logging functionality."""

    def __init__(self, logging_config_file: Path, logger_name: str) -> None:
        setup_logger(logging_config_file)
        self.logger = logging.getLogger(logger_name)

    def error(self, message: str, exc_info: Optional[bool] = None) -> None:
        self.logger.error(message, exc_info=exc_info)

    def exception(self, message: str, exc_info: Optional[bool] = None) -> None:
        self.logger.exception(message, exc_info=exc_info)

    def debug(self, message: str, exc_info: Optional[bool] = None) -> None:
        self.logger.debug(message, exc_info=exc_info)

    def warning(self, message: str, exc_info: Optional[bool] = None) -> None:
        self.logger.warning(message, exc_info=exc_info)

    def info(self, message: str, exc_info: Optional[bool] = None) -> None:  # noqa: WPS110
        self.logger.info(message, exc_info=exc_info)
