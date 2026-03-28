from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import instructor
import pytest
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel

from src.infrastructure.db.redis.client import RedisClient
from src.infrastructure.db.redis.repository import BaseRedisRepository
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from tests.unit.infrastructure.base_graph.graph_mock import BaseGraphTest


@pytest.fixture
def test_schemas() -> tuple[type[BaseModel], type[BaseModel]]:
    """Return basic state and output schemas for graph tests."""
    from tests.schema import DummyOutputSchema, DummyStateSchema

    return DummyStateSchema, DummyOutputSchema


@pytest.fixture(name="structured_prompts")
def fixture_structured_prompts(tmp_path: Path) -> Path:
    """Fixture that creates a temporary structured prompts directory for testing."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    categories: dict[str, dict[str, str]] = {
        "marketing": {
            "launch": "## Launch plan\nKeep it short.",
            "email": "## Email copy\nRespect privacy.",
        },
        "support": {
            "greeting": "## Hello\nHow can I assist you today?",
        },
    }

    for category_name, templates in categories.items():
        category_dir = prompts_dir / category_name
        category_dir.mkdir()
        for template_name, body in templates.items():
            file_path = category_dir / f"{template_name}.md"
            file_path.write_text(body, encoding="utf-8")

    return prompts_dir


@pytest.fixture
def mock_base_graph() -> BaseGraph:
    """Provide a fresh compiled graph stub for each test."""
    compiled_graph = MagicMock(spec=BaseGraph)
    compiled_graph.ainvoke = AsyncMock()
    return compiled_graph


@pytest.fixture
def mock_prompt_builder() -> BasePromptManager:
    """Provide a mocked prompt builder for graph initialization."""
    return MagicMock(spec=BasePromptManager)


@pytest.fixture
def mock_instructor_client() -> instructor.AsyncInstructor:
    mock_instructor_client = MagicMock()
    return mock_instructor_client


@pytest.fixture
def mock_redis_client() -> Generator[Any, Any, Any]:
    """Provide a RedisClient with mocked underlying Redis connection."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        yield RedisClient(redis_url="redis://:test@localhost:6379/0")


@pytest.fixture
def mock_redis_repository(mock_redis_client: Any) -> Any:
    """Provide a BaseRedisRepository backed by the mocked RedisClient."""
    return BaseRedisRepository(mock_redis_client)


@pytest.fixture
def test_base_graph(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> BaseGraphTest:
    """Instantiate the concrete test graph used across initialization tests."""
    state_schema, output_schema = test_schemas

    return BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        langfuse_handler=MagicMock(spec=CallbackHandler),
    )
