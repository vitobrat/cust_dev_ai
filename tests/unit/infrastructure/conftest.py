from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import instructor
import pytest
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel

from src.configs.config import RabbitMQConfigs
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from src.infrastructure.rabbitmq.client import RabbitMQClient
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


@pytest.fixture
def rabbitmq_configs() -> RabbitMQConfigs:
    """Provide a mock RabbitMQConfigs instance with test values."""
    configs = MagicMock(spec=RabbitMQConfigs)
    configs.host = "localhost"
    configs.port = 5672
    configs.vhost = "/"
    configs.user = "guest"
    configs.password = "guest"
    return configs


@pytest.fixture
def mock_default_exchange() -> AsyncMock:
    """Provide a mock AMQP default exchange."""
    exchange = AsyncMock()
    exchange.publish = AsyncMock()
    return exchange


@pytest.fixture
def mock_queue() -> AsyncMock:
    """Provide a mock AMQP queue."""
    queue = AsyncMock(spec=AbstractQueue)
    queue.consume = AsyncMock()
    return queue


@pytest.fixture
def mock_channel(
    mock_default_exchange: AsyncMock,
    mock_queue: AsyncMock,
) -> AsyncMock:
    """Provide a mock AMQP channel with default exchange and declare_queue."""
    channel = AsyncMock(spec=AbstractChannel)
    channel.default_exchange = mock_default_exchange
    channel.declare_queue = AsyncMock(return_value=mock_queue)
    return channel


@pytest.fixture
def mock_connection(mock_channel: AsyncMock) -> AsyncMock:
    """Provide a mock robust AMQP connection returning mock_channel."""
    connection = AsyncMock(spec=AbstractRobustConnection)
    connection.channel = AsyncMock(return_value=mock_channel)
    connection.close = AsyncMock()
    return connection


@pytest.fixture
def rabbitmq_client(rabbitmq_configs: RabbitMQConfigs) -> RabbitMQClient:
    """Provide a fresh RabbitMQClient without active connection."""
    return RabbitMQClient(configs=rabbitmq_configs)


@pytest.fixture
def connected_rabbitmq_client(
    rabbitmq_client: RabbitMQClient,
    mock_connection: AsyncMock,
    mock_channel: AsyncMock,
) -> RabbitMQClient:
    """Provide a RabbitMQClient with pre-injected mock connection and channel."""
    rabbitmq_client._connection = mock_connection
    rabbitmq_client._channel = mock_channel
    return rabbitmq_client


@pytest.fixture
def mock_incoming_message() -> AsyncMock:
    """Provide a mock incoming AMQP message with process() context manager."""
    message = AsyncMock(spec=AbstractIncomingMessage)
    message.reply_to = "reply-queue"
    message.correlation_id = "corr-123"
    message.body = b'{"key": "value"}'

    process_cm = AsyncMock()
    process_cm.__aenter__ = AsyncMock(return_value=None)
    process_cm.__aexit__ = AsyncMock(return_value=False)
    message.process = MagicMock(return_value=process_cm)

    return message
