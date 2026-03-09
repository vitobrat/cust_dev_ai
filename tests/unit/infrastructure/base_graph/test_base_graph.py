"""
Unit tests for BaseGraph initialization and processing logic, using a concrete subclass to verify behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from src.configs.consts import DEFAULT_GRAPH_RECURSION_LIMIT
from src.infrastructure.exceptions import GraphError
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from tests.schema import DummyOutputSchema, DummyStateSchema
from tests.unit.infrastructure.base_graph.graph_mock import BaseGraphTest


def test_base_graph_initializes_dependencies_and_builds_graph(
    test_base_graph: BaseGraphTest,
    mock_prompt_builder: BasePromptManager,
    mock_llm_adapter: LLMAdapter,
) -> None:
    """Ensure constructor wires dependencies and compiles the graph."""
    assert test_base_graph._llm_adapter is mock_llm_adapter
    assert test_base_graph._prompt_builder is mock_prompt_builder
    assert test_base_graph.configured is True
    assert test_base_graph._recursion_limit == DEFAULT_GRAPH_RECURSION_LIMIT


def test_base_graph_accepts_custom_recursion_limit(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify the recursion limit can be overridden through the constructor."""
    state_schema, output_schema = test_schemas
    custom_limit = 42

    graph = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        recursion_limit=custom_limit,
    )

    assert graph._recursion_limit == custom_limit


def test_base_graph_handles_invalid_recursion_limit_on_init(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify invalid recursion limit falls back to default during initialization."""
    state_schema, output_schema = test_schemas

    # Test with negative value
    graph_negative = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        recursion_limit=-5,
    )
    assert graph_negative._recursion_limit == DEFAULT_GRAPH_RECURSION_LIMIT

    # Test with zero
    graph_zero = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        recursion_limit=0,
    )
    assert graph_zero._recursion_limit == DEFAULT_GRAPH_RECURSION_LIMIT


def test_base_graph_accepts_langfuse_handler(
    test_base_graph: BaseGraphTest,
) -> None:
    """Verify langfuse handler is stored correctly."""
    assert test_base_graph._langfuse_handler is not None


def test_base_graph_stores_output_schema(
    test_base_graph: BaseGraphTest,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
) -> None:
    """Verify output schema is stored correctly."""
    _, output_schema = test_schemas

    assert test_base_graph.output_schema is output_schema


def test_recursion_limit_setter_with_valid_value(test_base_graph: BaseGraphTest) -> None:
    """Verify recursion_limit property setter accepts valid positive integers."""
    test_base_graph.recursion_limit = 100
    assert test_base_graph._recursion_limit == 100
    assert test_base_graph.recursion_limit == 100


def test_recursion_limit_setter_rejects_negative_value(test_base_graph: BaseGraphTest) -> None:
    """Verify recursion_limit property setter rejects negative values."""
    with pytest.raises(ValueError, match="Recursion limit must be a positive integer"):
        test_base_graph.recursion_limit = -10


def test_recursion_limit_setter_rejects_zero(test_base_graph: BaseGraphTest) -> None:
    """Verify recursion_limit property setter rejects zero."""
    with pytest.raises(ValueError, match="Recursion limit must be a positive integer"):
        test_base_graph.recursion_limit = 0


def test_recursion_limit_setter_rejects_non_integer(test_base_graph: BaseGraphTest) -> None:
    """Verify recursion_limit property setter rejects non-integer values."""
    with pytest.raises(ValueError, match="Recursion limit must be a positive integer"):
        test_base_graph.recursion_limit = "invalid"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="Recursion limit must be a positive integer"):
        test_base_graph.recursion_limit = 3.78  # type: ignore[assignment]


@pytest.mark.asyncio
async def test_process_executes_graph_successfully(test_base_graph: BaseGraphTest) -> None:
    """Verify process method executes graph and returns validated output."""
    input_state = DummyStateSchema(input="test input")
    expected_output = {"output": "test output"}

    test_base_graph.graph.ainvoke = AsyncMock(return_value=expected_output)

    graph_result = await test_base_graph.process(input_state)

    assert isinstance(graph_result, DummyOutputSchema)
    assert graph_result.output == "test output"
    test_base_graph.graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_process_passes_recursion_limit_to_graph(test_base_graph: BaseGraphTest) -> None:
    """Verify process method passes recursion limit in config."""
    input_state = DummyStateSchema(input="test")
    test_base_graph.graph.ainvoke = AsyncMock(return_value={"output": "result"})

    await test_base_graph.process(input_state)

    call_args = test_base_graph.graph.ainvoke.call_args
    assert call_args[1]["config"]["recursion_limit"] == DEFAULT_GRAPH_RECURSION_LIMIT


@pytest.mark.asyncio
async def test_process_passes_langfuse_handler_when_present(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify process method includes langfuse handler in callbacks when configured."""
    state_schema, output_schema = test_schemas
    mock_handler = MagicMock(spec=CallbackHandler)

    graph = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        langfuse_handler=mock_handler,
    )
    graph.graph.ainvoke = AsyncMock(return_value={"output": "result"})

    input_state = DummyStateSchema(input="test")
    await graph.process(input_state)

    call_args = graph.graph.ainvoke.call_args
    assert "callbacks" in call_args[1]["config"]
    assert mock_handler in call_args[1]["config"]["callbacks"]


@pytest.mark.asyncio
async def test_process_does_not_pass_callbacks_when_no_langfuse_handler(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify process method does not include callbacks when langfuse handler is None."""
    state_schema, output_schema = test_schemas
    graph = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
    )

    graph.graph.ainvoke = AsyncMock(return_value={"output": "result"})

    input_state = DummyStateSchema(input="test")
    await graph.process(input_state)

    call_args = graph.graph.ainvoke.call_args
    assert "callbacks" not in call_args[1]["config"]


@pytest.mark.asyncio
async def test_process_raises_graph_error_on_graph_execution_failure(
    test_base_graph: BaseGraphTest,
) -> None:
    """Verify process method wraps graph execution exceptions in GraphError."""
    input_state = DummyStateSchema(input="test")
    test_base_graph.graph.ainvoke = AsyncMock(side_effect=RuntimeError("Graph failed"))

    with pytest.raises(GraphError, match="Error during BaseGraphTest execution"):
        await test_base_graph.process(input_state)


@pytest.mark.asyncio
async def test_process_raises_graph_error_when_graph_returns_none(
    test_base_graph: BaseGraphTest,
) -> None:
    """Verify process method raises GraphError when graph returns None."""
    input_state = DummyStateSchema(input="test")
    test_base_graph.graph.ainvoke = AsyncMock(return_value=None)

    with pytest.raises(GraphError, match="Graph BaseGraphTest returned None response"):
        await test_base_graph.process(input_state)


@pytest.mark.asyncio
async def test_process_raises_graph_error_on_output_validation_failure(
    test_base_graph: BaseGraphTest,
) -> None:
    """Verify process method raises GraphError when output validation fails."""
    input_state = DummyStateSchema(input="test")
    # Return invalid output that doesn't match schema
    test_base_graph.graph.ainvoke = AsyncMock(return_value={"invalid_field": "value"})

    with pytest.raises(GraphError, match="Failed to validate output for BaseGraphTest"):
        await test_base_graph.process(input_state)


@pytest.mark.asyncio
async def test_process_uses_custom_recursion_limit(
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify process method uses custom recursion limit when set."""
    state_schema, output_schema = test_schemas
    custom_limit = 77

    graph = BaseGraphTest(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=mock_llm_adapter,
        prompt_builder=mock_prompt_builder,
        recursion_limit=custom_limit,
    )
    graph.graph.ainvoke = AsyncMock(return_value={"output": "result"})

    input_state = DummyStateSchema(input="test")
    await graph.process(input_state)

    call_args = graph.graph.ainvoke.call_args
    assert call_args[1]["config"]["recursion_limit"] == custom_limit


def test_build_graph_calls_configurate_graph(
    test_base_graph: BaseGraphTest,
) -> None:
    """Verify _build_graph calls _configurate_graph during initialization."""

    assert test_base_graph.configured is True


def test_build_graph_returns_compiled_graph(test_base_graph: BaseGraphTest) -> None:
    """Verify _build_graph returns a CompiledStateGraph instance."""
    assert isinstance(test_base_graph.graph, CompiledStateGraph)
