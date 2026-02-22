"""
Base prompt manager for loading and managing prompt templates.

This module provides a base class for prompt management that can be
extended for domain-specific use cases. Prompts are loaded from a directory
structure where each subdirectory represents a category containing .md files.
"""

from pathlib import Path
from typing import Final, final

from src.configs.log.logger import get_logger


class BasePromptManager:
    """Base class for managing prompt templates.

    This class handles loading prompt templates from a directory structure
    and provides methods to retrieve them. Subclasses should implement
    domain-specific prompt building logic.

    The directory structure should be:
        prompts_dir/
            category1/
                template1.md
                template2.md
            category2/
                template3.md

    Args:
        prompts_dir: Path to the directory containing prompt templates.

    Raises:
        FileNotFoundError: If the prompts directory does not exist.
        ValueError: If the prompts directory is not a directory.
    """

    def __init__(self, prompts_dir: Path) -> None:
        """Initialize the prompt manager and load templates.

        Args:
            prompts_dir: Path to the directory containing prompt templates.

        Raises:
            FileNotFoundError: If the prompts directory does not exist.
            ValueError: If the prompts directory is not a directory.
        """
        self._prompts_dir: Final[Path] = prompts_dir
        self._prompts: dict[str, dict[str, str]] = {}
        self._logger: Final = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
        )

        self._validate_prompts_dir()
        self._load_prompts()

    @final
    def get_template(self, category: str, template_name: str) -> str:
        """Retrieve a prompt template by category and name.

        Args:
            category: The category (subdirectory) name.
            template_name: The template (file stem) name.

        Returns:
            The template content as a string, or an empty string if not found.
        """
        if category not in self._prompts:
            self._logger.error(f"Category not found: {category}")
            return ""

        if template_name not in self._prompts[category]:
            self._logger.error(
                f"Template not found: {category}/{template_name}",
            )
            return ""

        return self._prompts[category][template_name]

    @final
    def has_template(self, category: str, template_name: str) -> bool:
        """Check if a specific template exists.

        Args:
            category: The category name.
            template_name: The template name.

        Returns:
            True if the template exists, False otherwise.
        """
        return category in self._prompts and template_name in self._prompts[category]

    def _load_prompts(self) -> None:
        """Load all .md files from subdirectories into memory.

        Each subdirectory represents a category, and each .md file within
        represents a template. Templates are stored in a nested dictionary
        structure: {category: {template_name: content}}.
        """
        loaded_count = 0

        for category_dir in self._prompts_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            self._prompts[category_name] = self._load_prompts_in_category(category_dir)

        self._logger.info(
            f"Loaded {loaded_count} prompt templates from {self._prompts_dir}",
        )

    def _load_prompts_in_category(self, category_dir: Path) -> dict[str, str]:
        """Load all .md files from a specific category directory.

        Args:
            category_dir: Path to the category directory.

        Returns:
            A dictionary mapping template names to their content.
        """
        category_prompts = {}
        for md_file in category_dir.glob("*.md"):
            template_name = md_file.stem
            try:
                prompt_content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                self._logger.warning(
                    f"Failed to load prompt {md_file}: {exc}",
                )
                prompt_content = ""
            category_prompts[template_name] = prompt_content

        return category_prompts

    def _validate_prompts_dir(self) -> None:
        """Validate that the prompts directory exists and is a directory.

        Raises:
            FileNotFoundError: If the prompts directory does not exist.
            ValueError: If the prompts directory is not a directory.
        """
        if not self._prompts_dir.exists():
            error_msg = f"Prompts directory does not exist: {self._prompts_dir}"
            self._logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not self._prompts_dir.is_dir():
            error_msg = f"Prompts path is not a directory: {self._prompts_dir}"
            self._logger.error(error_msg)
            raise ValueError(error_msg)
