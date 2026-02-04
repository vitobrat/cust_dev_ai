import os
from pathlib import Path

_DEFAULT_PROJECT_PATH = Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', _DEFAULT_PROJECT_PATH))

valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
