from pathlib import Path

from alembic import command
from alembic.config import Config

from src.configs.consts import PROJECT_ROOT


def run_migrations(connection_url: str) -> None:
    alembic_cfg = Config(Path(PROJECT_ROOT, "alembic.ini"))

    sync_url = connection_url.replace("asyncpg", "psycopg2")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    command.upgrade(alembic_cfg, "head")
