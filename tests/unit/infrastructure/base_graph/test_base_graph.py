"""
Unit tests for BaseGraph initialization and processing logic, using a concrete subclass to verify behavior.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from src.configs.consts import _DEFAULT_GRAPH_RECURSION_LIMIT
from src.infrastructure.graph.base_graph import GraphError
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from tests.schema import DummyOutputSchema, DummyStateSchema
from tests.unit.infrastructure.base_graph.graph_mock import MockBaseGraph
from tests.unit.infrastructure.utils import make_graph


def test_base_graph_initializes_dependencies_and_builds_graph(
    concrete_graph: MockBaseGraph,
    mock_compiled_state_graph: CompiledStateGraph,
    mock_prompt_builder: BasePromptManager,
    mock_llm_adapter: LLMAdapter,
) -> None:
    """Ensure constructor wires dependencies and compiles the graph."""

    assert concrete_graph._llm_adapter is mock_llm_adapter
    assert concrete_graph._prompt_builder is mock_prompt_builder
    assert concrete_graph.graph is mock_compiled_state_graph
    assert concrete_graph.configured is True
    assert concrete_graph._recursion_limit == _DEFAULT_GRAPH_RECURSION_LIMIT


def test_base_graph_accepts_custom_recursion_limit(
    mock_compiled_state_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify the recursion limit can be overridden through the constructor."""

    graph = make_graph(
        mock_compiled_state_graph,
        test_schemas,
        mock_llm_adapter,
        mock_prompt_builder,
        recursion_limit=5,
    )
    assert graph._recursion_limit == 5


@pytest.mark.asyncio
async def test_process_invokes_graph_and_validates_output(
    concrete_graph: MockBaseGraph,
    mock_compiled_state_graph: CompiledStateGraph,
) -> None:
    """Ensure process forwards state and returns validated data."""

    mock_compiled_state_graph.ainvoke.return_value = {"output": "done"}
    payload = DummyStateSchema(input="value").model_dump()
    result = await concrete_graph.process(payload)
    assert isinstance(result, DummyOutputSchema)
    assert result.output == "done"
    mock_compiled_state_graph.ainvoke.assert_awaited_once_with(
        payload,
        config={"recursion_limit": concrete_graph._recursion_limit},
    )


@pytest.mark.asyncio
async def test_process_includes_langfuse_handler_in_callbacks(
    mock_compiled_state_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Verify langfuse handler is added to the config callbacks list."""

    handler = MagicMock(spec=CallbackHandler)
    graph = make_graph(
        mock_compiled_state_graph,
        test_schemas,
        mock_llm_adapter,
        mock_prompt_builder,
        langfuse_handler=handler,
    )
    mock_compiled_state_graph.ainvoke.return_value = {"output": "ok"}
    state = DummyStateSchema(input="value").model_dump()
    await graph.process(state)
    config = mock_compiled_state_graph.ainvoke.call_args.kwargs["config"]
    assert config["recursion_limit"] == graph._recursion_limit
    assert config["callbacks"] == [handler]


@pytest.mark.asyncio
async def test_process_wraps_graph_invocation_errors(
    mock_compiled_state_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Ensure unexpected graph exceptions are raised as GraphError."""

    graph = make_graph(
        mock_compiled_state_graph,
        test_schemas,
        mock_llm_adapter,
        mock_prompt_builder,
    )
    mock_compiled_state_graph.ainvoke.side_effect = ValueError("boom")
    with pytest.raises(GraphError):
        await graph.process(DummyStateSchema(input="value").model_dump())


@pytest.mark.asyncio
async def test_process_raises_when_graph_returns_none(
    mock_compiled_state_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Invalid None responses from the graph should surface as GraphError."""

    graph = make_graph(
        mock_compiled_state_graph,
        test_schemas,
        mock_llm_adapter,
        mock_prompt_builder,
    )
    mock_compiled_state_graph.ainvoke.return_value = None
    with pytest.raises(GraphError):
        await graph.process(DummyStateSchema(input="value").model_dump())


@pytest.mark.asyncio
async def test_process_raises_on_output_validation_failure(
    mock_compiled_state_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    mock_llm_adapter: LLMAdapter,
    mock_prompt_builder: BasePromptManager,
) -> None:
    """Ensure schema validation failures are reported via GraphError."""

    graph = make_graph(
        mock_compiled_state_graph,
        test_schemas,
        mock_llm_adapter,
        mock_prompt_builder,
    )
    mock_compiled_state_graph.ainvoke.return_value = {"unexpected": "value"}
    with pytest.raises(GraphError):
        await graph.process(DummyStateSchema(input="value").model_dump())
