from __future__ import annotations

from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from src.infrastructure.llm.llm_adapter import LLMAdapter, LLMProtocol
from tests.schema import StructuredOutputSchema
from tests.unit.infrastructure.utils import async_iter, collect_stream


@pytest.mark.asyncio
async def test_ainvoke_returns_content(mock_llm: LLMProtocol) -> None:
    """Extract content from the LLM response object."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm.ainvoke.return_value = AIMessage(content="hello")

    result = await adapter.ainvoke(messages, temperature=0.2)

    assert result == "hello"
    mock_llm.ainvoke.assert_awaited_once_with(messages, temperature=0.2)


@pytest.mark.asyncio
async def test_ainvoke_wraps_errors(mock_llm: LLMProtocol) -> None:
    """Wrap underlying errors in ``RuntimeError`` with context."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm.ainvoke.side_effect = ValueError("boom")

    with pytest.raises(RuntimeError) as excinfo:
        await adapter.ainvoke(messages)

    assert "Failed to invoke LLM" in str(excinfo.value)


def test_bind_tools_creates_new_adapter(mock_llm: LLMProtocol) -> None:
    """Binding tools must produce a fresh adapter wrapping the bound LLM."""

    adapter = LLMAdapter(mock_llm)
    bound_llm = MagicMock(spec_set=LLMProtocol)
    mock_llm.bind_tools.return_value = bound_llm

    bound_adapter = adapter.bind_tools([])

    assert bound_adapter is not adapter
    assert bound_adapter._llm is bound_llm


def test_with_config_returns_new_adapter(mock_llm: LLMProtocol) -> None:
    """Config updates should wrap the configured LLM without mutating original."""

    adapter = LLMAdapter(mock_llm)
    configured_llm = MagicMock(spec_set=LLMProtocol)
    mock_llm.with_config.return_value = configured_llm
    config: dict[str, Any] = {"temperature": 0.5}

    configured_adapter = adapter.with_config(config)

    assert configured_adapter is not adapter
    assert configured_adapter._llm is configured_llm


@pytest.mark.asyncio
async def test_astream_delegates_and_collects_chunks(mock_llm: LLMProtocol) -> None:
    """Ensure ``astream`` yields the messages produced by the wrapped LLM."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    expected = [AIMessage(content="Hello"), AIMessage(content="world")]
    stream = AsyncMock(return_value=async_iter(expected))
    mock_llm.astream = stream

    collected = await collect_stream(adapter, messages, temperature=0.0)

    assert collected == expected
    stream.assert_awaited_once_with(messages, temperature=0.0)


@pytest.mark.asyncio
async def test_astream_wraps_errors(mock_llm: LLMProtocol) -> None:
    """Errors while streaming should surface as ``RuntimeError``."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm.astream.side_effect = ValueError("boom")

    with pytest.raises(RuntimeError) as excinfo:
        await collect_stream(adapter, messages)

    assert "Failed to stream from LLM" in str(excinfo.value)


@pytest.mark.asyncio
async def test_ainvoke_with_tools_binds_then_invokes(mock_llm: LLMProtocol) -> None:
    """``ainvoke_with_tools`` should bind tools before invoking."""

    adapter = LLMAdapter(mock_llm)
    bound_adapter = MagicMock(spec_set=LLMAdapter)
    bound_adapter.ainvoke = AsyncMock(return_value=AIMessage(content="done"))
    adapter.bind_tools = MagicMock(return_value=bound_adapter)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]

    result = await adapter.ainvoke_with_tools(messages, tools=[])

    assert result == "done"
    bound_adapter.ainvoke.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_structured_ainvoke_returns_schema_instance(mock_llm: LLMProtocol) -> None:
    """Structured invocation should honor the provided schema."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value=StructuredOutputSchema(text="done"))
    mock_llm.with_structured_output.return_value = structured_llm

    result = await adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert isinstance(result, StructuredOutputSchema)
    structured_llm.ainvoke.assert_awaited_once_with(messages)


@pytest.mark.asyncio
async def test_structured_ainvoke_include_raw_parsing_error(mock_llm: LLMProtocol) -> None:
    """Including raw results surfaces parsing errors when requested."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value={"foo": "bar", "parsing_error": "bad json"})
    mock_llm.with_structured_output.return_value = structured_llm

    result = await adapter.structured_ainvoke(messages, StructuredOutputSchema, include_raw=True)

    assert result["parsing_error"] == "bad json"


@pytest.mark.asyncio
async def test_structured_output_not_supported(mock_llm: LLMProtocol) -> None:
    """Lack of structured output support should raise a runtime error."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    mock_llm.with_structured_output.side_effect = AttributeError("nope")

    with pytest.raises(RuntimeError) as excinfo:
        await adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert "does not support structured output" in str(excinfo.value)


@pytest.mark.asyncio
async def test_structured_ainvoke_propagates_invocation_errors(mock_llm: LLMProtocol) -> None:
    """Invocation failures should surface as runtime errors."""

    adapter = LLMAdapter(mock_llm)
    messages: List[BaseMessage] = [AIMessage(content="prompt")]
    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))
    mock_llm.with_structured_output.return_value = structured_llm

    with pytest.raises(RuntimeError) as excinfo:
        await adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert "Failed to invoke structured LLM" in str(excinfo.value)
