"""Unit tests for LLMAdapter with instructor integration."""

from __future__ import annotations

from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import instructor
import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

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
    llm_response = await llm_adapter.ainvoke(messages)

    assert llm_response == "hello"
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
    mock_llm = container.infrastructure.llm()
    mock_llm.ainvoke.return_value = AIMessage(content="done")

    llm_adapter = container.infrastructure.llm_adapter()
    llm_response = await llm_adapter.ainvoke_with_tools(messages, tools=[])

    assert llm_response == "done"
    mock_llm.bind_tools.assert_called_once()
    mock_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_structured_ainvoke_with_instructor_client(
    container: RootContainer,
    mock_instructor_client: instructor.AsyncInstructor,
) -> None:
    """When instructor client is available, use it for structured output."""
    expected_result = StructuredOutputSchema(text="instructor response")
    mock_instructor_client.chat.completions.create = AsyncMock(return_value=expected_result)

    messages: List[BaseMessage] = [HumanMessage(content="test prompt")]

    with patch("src.infrastructure.llm.llm_adapter.instructor.from_openai", return_value=mock_instructor_client):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=2)

    assert llm_response == expected_result
    mock_instructor_client.chat.completions.create.assert_awaited_once()
    create_chat_complection = mock_instructor_client.chat.completions
    call_kwargs = create_chat_complection.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4"
    assert call_kwargs["response_model"] == StructuredOutputSchema
    assert call_kwargs["max_retries"] == 2
    assert call_kwargs["messages"] == [{"role": "user", "content": "test prompt"}]


@pytest.mark.asyncio
async def test_structured_ainvoke_without_instructor_falls_back(container: RootContainer) -> None:
    """When instructor client is unavailable, fall back to base structured invoke."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test prompt")]
    expected_result = StructuredOutputSchema(text="fallback response")

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value={"parsed": expected_result})
    mock_llm.with_structured_output.return_value = structured_llm

    # Patch instructor to raise AttributeError simulating missing async_client
    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema)

    assert llm_response == expected_result
    mock_llm.with_structured_output.assert_called_once_with(
        StructuredOutputSchema,
        include_raw=True,
        method="json_mode",
    )


@pytest.mark.asyncio
async def test_base_structured_ainvoke_success_on_first_attempt(container: RootContainer) -> None:
    """Base structured invoke returns parsed result on first successful attempt."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test")]
    expected_result = StructuredOutputSchema(text="success")

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(return_value={"parsed": expected_result})
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=3)

    assert llm_response == expected_result
    structured_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_base_structured_ainvoke_retries_on_parsing_error(container: RootContainer) -> None:
    """Base structured invoke retries when parsing fails, then succeeds."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test")]
    expected_result = StructuredOutputSchema(text="success after retry")

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(
        side_effect=[
            {
                "parsed": None,
                "parsing_error": "Invalid JSON",
                "raw": AIMessage(content='{"invalid": json}'),
            },
            {"parsed": expected_result},
        ],
    )
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=3)

    assert llm_response == expected_result
    assert structured_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_base_structured_ainvoke_uses_json_repair(container: RootContainer) -> None:
    """Base structured invoke attempts json-repair before retrying LLM."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test")]

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(
        return_value={
            "parsed": None,
            "parsing_error": "Invalid JSON",
            "raw": AIMessage(content='{"text": "repaired"}'),
        },
    )
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        with patch("src.infrastructure.llm.llm_adapter.repair_json") as mock_repair:
            mock_repair.return_value = '{"text": "repaired"}'

            llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
            llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=3)

            assert llm_response.text == "repaired"
            mock_repair.assert_called_once_with('{"text": "repaired"}')
            # Should not retry LLM if repair succeeds
            structured_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_base_structured_ainvoke_appends_error_feedback(container: RootContainer) -> None:
    """Base structured invoke appends validation error as feedback for retry."""
    messages: List[BaseMessage] = [HumanMessage(content="test")]
    expected_result = StructuredOutputSchema(text="corrected")

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(
        side_effect=[
            {
                "parsed": None,
                "parsing_error": "Missing required field: text",
                "raw": AIMessage(content='{"wrong": "field"}'),
            },
            {"parsed": expected_result},
        ],
    )
    mock_llm = container.infrastructure.llm()
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        with patch("src.infrastructure.llm.llm_adapter.repair_json", side_effect=Exception("repair failed")):
            llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
            llm_response = await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=3)

    assert llm_response == expected_result

    args, _ = structured_llm.ainvoke.call_args_list[1]
    second_call_messages = args[0]
    assert len(second_call_messages) == 3
    assert isinstance(second_call_messages[1], AIMessage)
    assert isinstance(second_call_messages[2], HumanMessage)
    assert "validation error" in second_call_messages[2].content.lower()


@pytest.mark.asyncio
async def test_base_structured_ainvoke_exhausts_retries(container: RootContainer) -> None:
    """Base structured invoke raises RuntimeError after exhausting all retries."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test")]

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(
        return_value={
            "parsed": None,
            "parsing_error": "Persistent error",
            "raw": AIMessage(content="bad output"),
        },
    )
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        with patch("src.infrastructure.llm.llm_adapter.repair_json", side_effect=Exception("repair failed")):
            llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()

            with pytest.raises(RuntimeError) as excinfo:
                await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=2)

            assert "Failed to get structured output after 2 attempts" in str(excinfo.value)
            assert structured_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_base_structured_ainvoke_handles_unexpected_exception(container: RootContainer) -> None:
    """Base structured invoke handles unexpected exceptions during invocation."""
    mock_llm = container.infrastructure.llm()

    messages: List[BaseMessage] = [HumanMessage(content="test")]

    structured_llm = MagicMock(spec_set=LLMProtocol)
    structured_llm.ainvoke = AsyncMock(side_effect=ValueError("unexpected error"))
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()

        with pytest.raises(RuntimeError) as excinfo:
            await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema, max_retries=2)

        assert "Failed to get structured output after 2 attempts" in str(excinfo.value)
        assert structured_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_structured_ainvoke_instructor_role_mapping(
    container: RootContainer,
    mock_instructor_client: instructor.AsyncInstructor,
) -> None:
    """Instructor integration correctly maps LangChain message types to OpenAI roles."""
    mock_instructor_client.chat.completions.create = AsyncMock(return_value=StructuredOutputSchema(text="response"))

    messages: List[BaseMessage] = [
        HumanMessage(content="user message"),
        AIMessage(content="assistant message"),
    ]

    with patch("src.infrastructure.llm.llm_adapter.instructor.from_openai", return_value=mock_instructor_client):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await llm_adapter.structured_ainvoke(messages, StructuredOutputSchema)
    create_chat_complection = mock_instructor_client.chat.completions.create
    call_kwargs = create_chat_complection.call_args.kwargs
    assert call_kwargs["messages"] == [
        {"role": "user", "content": "user message"},
        {"role": "assistant", "content": "assistant message"},
    ]


def test_setup_instructor_client_success(container: RootContainer) -> None:
    """Instructor client is set up when async_client is available."""
    mock_llm = container.infrastructure.llm()

    with patch("src.infrastructure.llm.llm_adapter.instructor.from_openai") as mock_from_openai:
        mock_instructor = MagicMock()
        mock_from_openai.return_value = mock_instructor

        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()

        assert llm_adapter._instructor_client == mock_instructor
        mock_from_openai.assert_called_once_with(mock_llm.async_client)


def test_setup_instructor_client_missing_async_client(container: RootContainer) -> None:
    """Instructor client is None when async_client is not available."""
    with patch(
        "src.infrastructure.llm.llm_adapter.instructor.from_openai",
        side_effect=AttributeError("no async_client"),
    ):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()

        assert llm_adapter._instructor_client is None


@pytest.mark.asyncio
async def test_structured_ainvoke_forwards_kwargs_to_instructor(
    container: RootContainer,
    mock_instructor_client: instructor.AsyncInstructor,
) -> None:
    """Extra kwargs are forwarded to instructor client."""
    mock_instructor_client.chat.completions.create = AsyncMock(return_value=StructuredOutputSchema(text="response"))

    messages: List[BaseMessage] = [HumanMessage(content="test")]

    with patch("src.infrastructure.llm.llm_adapter.instructor.from_openai", return_value=mock_instructor_client):
        llm_adapter: LLMAdapter = container.infrastructure.llm_adapter()
        await llm_adapter.structured_ainvoke(
            messages,
            StructuredOutputSchema,
            max_retries=5,
            temperature=0.7,  # noqa: WPS432
        )

    create_chat_complection = mock_instructor_client.chat.completions.create
    call_kwargs = create_chat_complection.call_args.kwargs
    assert call_kwargs["max_retries"] == 5
