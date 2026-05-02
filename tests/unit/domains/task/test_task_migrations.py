"""Unit tests for task-domain migration coverage."""

from pathlib import Path

from src.configs.consts import PROJECT_ROOT

_MIGRATIONS_DIR = Path(PROJECT_ROOT, "src", "migrations", "versions")


def test_interview_simulation_task_type_has_postgres_enum_migration() -> None:
    """The PostgreSQL tasktype enum must be migrated before this task can be persisted."""
    migration_payload = "\n".join(
        migration_path.read_text(encoding="utf-8") for migration_path in sorted(_MIGRATIONS_DIR.glob("*.py"))
    )

    assert "ALTER TYPE tasktype ADD VALUE" in migration_payload
    assert "INTERVIEW_SIMULATION" in migration_payload
