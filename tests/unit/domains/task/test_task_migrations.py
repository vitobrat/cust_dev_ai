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


def test_final_report_storage_has_postgres_migration() -> None:
    """The interview final_report JSONB column must be added by migration."""
    migration_payload = "\n".join(
        migration_path.read_text(encoding="utf-8") for migration_path in sorted(_MIGRATIONS_DIR.glob("*.py"))
    )

    assert 'op.add_column(\n        "interviews",' in migration_payload
    assert '"final_report"' in migration_payload
    assert "JSONB" in migration_payload


def test_task_input_params_discriminator_has_backfill_migration() -> None:
    """Legacy task payloads must be backfilled with the task_type discriminator."""
    migration_payload = "\n".join(
        migration_path.read_text(encoding="utf-8") for migration_path in sorted(_MIGRATIONS_DIR.glob("*.py"))
    )

    assert "jsonb_set" in migration_payload
    assert "'{task_type}'" in migration_payload
    assert "sub_interview_generation" in migration_payload
