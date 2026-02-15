from __future__ import annotations

from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMAdapter, LLMProtocol
from tests.schema import StructuredOutputSchema
from tests.unit.infrastructure.utils_infrastructure_test import (
    async_iter,
    collect_stream,
)


@pytest.mark.asyncio
async def test_ainvoke_returns_content(container: RootContainer) -> None:
    """Extract content from the LLM response object."""
    mock_llm = container.infrastructure.llm()
    mock_llm.ainvoke.return_value = AIMessage(content="hello")
    messages: List[BaseMessage] = [AIMessage(content="prompt")]

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    graph_result = await llm_adapter.ainvoke(messages)

    assert graph_result == "hello"
    mock_llm.ainvoke.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_ainvoke_wraps_errors(container: RootContainer) -> None:
    """Wrap underlying errors in ``RuntimeError`` with context."""
    mock_llm = container.infrastructure.llm()
    mock_llm.ainvoke.side_effect = ValueError("boom")
    messages: List[BaseMessage] = [AIMessage(content="prompt")]

    with pytest.raises(RuntimeError) as excinfo:
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await llm_adapter.ainvoke(messages)

    assert "Failed to invoke LLM" in str(excinfo.value)


def test_bind_tools_creates_new_adapter(container: RootContainer) -> None:
    """Binding tools must produce a fresh adapter wrapping the bound LLM."""
    bound_llm = MagicMock(spec_set=LLMProtocol)
    mock_llm = container.infrastructure.llm()
    mock_llm.bind_tools.return_value = bound_llm

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    bound_adapter = llm_adapter.bind_tools([])

    assert bound_adapter is not llm_adapter
    assert bound_adapter._llm is bound_llm


def test_with_config_returns_new_adapter(container: RootContainer) -> None:
    """Config updates should wrap the configured LLM without mutating original."""
    configured_llm = MagicMock(spec_set=LLMProtocol)
    mock_llm = container.infrastructure.llm()
    mock_llm.with_config.return_value = configured_llm
    config: dict[str, Any] = {"temperature": 0.5}

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    configured_adapter = llm_adapter.with_config(config)

    assert configured_adapter is not llm_adapter
    assert configured_adapter._llm is configured_llm


@pytest.mark.asyncio
async def test_astream_delegates_and_collects_chunks(container: RootContainer) -> None:
    """Ensure ``astream`` yields the messages produced by the wrapped LLM."""
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    expected = [AIMessage(content="Hello"), AIMessage(content="world")]
    stream = AsyncMock(return_value=async_iter(expected))
    mock_llm = container.infrastructure.llm()
    mock_llm.astream = stream

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    collected = await collect_stream(llm_adapter, messages)

    assert collected == expected
    stream.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_astream_wraps_errors(container: RootContainer) -> None:
    """Errors while streaming should surface as ``RuntimeError``."""
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm = container.infrastructure.llm()
    mock_llm.astream.side_effect = ValueError("boom")

    with pytest.raises(RuntimeError) as excinfo:
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await collect_stream(llm_adapter, messages)

    assert "Failed to stream from LLM" in str(excinfo.value)


@pytest.mark.asyncio
async def test_ainvoke_with_tools_binds_then_invokes(container: RootContainer) -> None:
    """``ainvoke_with_tools`` should bind tools before invoking."""
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    bound_adapter = MagicMock(spec_set=LLMAdapter)
    bound_adapter.ainvoke = AsyncMock(return_value=AIMessage(content="done"))

    llm_adapter = container.infrastructure.llm_adapter()
    llm_adapter.bind_tools = MagicMock(return_value=bound_adapter)
    graph_result = await llm_adapter.ainvoke_with_tools(messages, tools=[])

    assert graph_result == "done"
    bound_adapter.ainvoke.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_structured_ainvoke_returns_schema_instance(container: RootContainer) -> None:
    """Structured invocation should honor the provided schema."""
    mock_llm = container.infrastructure.llm()
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value=StructuredOutputSchema(text="done"))
    mock_llm.with_structured_output.return_value = structured_llm

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    graph_result = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert isinstance(graph_result, StructuredOutputSchema)
    structured_llm.ainvoke.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_structured_ainvoke_include_raw_parsing_error(container: RootContainer) -> None:
    """Including raw results surfaces parsing errors when requested."""
    mock_llm = container.infrastructure.llm()
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value={"foo": "bar", "parsing_error": "bad json"})
    mock_llm.with_structured_output.return_value = structured_llm

    llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
    graph_result = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, include_raw=True)

    assert graph_result["parsing_error"] == "bad json"


@pytest.mark.asyncio
async def test_structured_output_not_supported(container: RootContainer) -> None:
    """Lack of structured output support should raise a runtime error."""
    mock_llm = container.infrastructure.llm()
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm.with_structured_output.side_effect = AttributeError("nope")

    with pytest.raises(RuntimeError) as excinfo:
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert "does not support structured output" in str(excinfo.value)


@pytest.mark.asyncio
async def test_structured_ainvoke_propagates_invocation_errors(container: RootContainer) -> None:
    """Invocation failures should surface as runtime errors."""
    mock_llm = container.infrastructure.llm()
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))
    mock_llm.with_structured_output.return_value = structured_llm

    with pytest.raises(RuntimeError) as excinfo:
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert "Failed to invoke structured LLM" in str(excinfo.value)
