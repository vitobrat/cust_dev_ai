from pathlib import Path

import pytest

from src.infrastructure.prompt.base_prompt_manager import BasePromptManager


def test_init_raises_for_missing_directory(tmp_path: Path) -> None:
    """Test that initializing BasePromptManager with a non-existent directory raises FileNotFoundError."""
    missing_path = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        BasePromptManager(missing_path)


def test_init_raises_for_file_path(tmp_path: Path) -> None:
    """Test that initializing BasePromptManager with a file path instead of a directory raises ValueError."""
    file_path = tmp_path / "not_a_dir.md"
    file_path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError):
        BasePromptManager(file_path)


def test_loading_templates_creates_expected_entries(structured_prompts: Path) -> None:
    """Test that BasePromptManager correctly loads templates from the structured prompts directory."""
    manager = BasePromptManager(structured_prompts)

    assert manager.has_template("marketing", "launch") is True
    assert manager.get_template("marketing", "launch") == "## Launch plan\nKeep it short."
    assert manager.has_template("marketing", "email") is True
    assert manager.get_template("marketing", "email") == "## Email copy\nRespect privacy."
    assert manager.has_template("support", "greeting") is True
    assert manager.get_template("support", "greeting") == "## Hello\nHow can I assist you today?"


def test_get_template_missing_cases(structured_prompts: Path) -> None:
    """
    Test that BasePromptManager returns False for has_template and empty string for get_template
    when templates are missing.
    """
    manager = BasePromptManager(structured_prompts)

    assert manager.has_template("nonexistent", "launch") is False
    assert manager.get_template("nonexistent", "launch") == ""
    assert manager.has_template("marketing", "unknown") is False
    assert manager.get_template("marketing", "unknown") == ""


def test_handles_unreadable_file(tmp_path: Path) -> None:
    """Test that BasePromptManager handles unreadable files gracefully by returning an empty string."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    broken_category = prompts_dir / "broken"
    broken_category.mkdir()
    broken_file = broken_category / "corrupted.md"
    broken_file.write_bytes(b"\xff\xfe")

    manager = BasePromptManager(prompts_dir)

    assert manager.has_template("broken", "corrupted") is True
    assert manager.get_template("broken", "corrupted") == ""


def test_ignores_non_directory_entries(tmp_path: Path) -> None:
    """Test that BasePromptManager ignores non-directory entries in the prompts directory."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    stray_file = prompts_dir / "notes.txt"
    stray_file.write_text("ignore", encoding="utf-8")
    category_dir = prompts_dir / "category"
    category_dir.mkdir()
    template_file = category_dir / "template.md"
    template_file.write_text("content", encoding="utf-8")

    manager = BasePromptManager(prompts_dir)

    assert manager.has_template("category", "template") is True
    assert manager.get_template("category", "template") == "content"
