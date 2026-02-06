from collections.abc import AsyncIterable
from typing import Any, List

from langchain_core.messages import AIMessage, BaseMessage

from src.infrastructure.llm.llm_adapter import LLMAdapter


async def _collect_stream(adapter: LLMAdapter, messages: List[BaseMessage], **kwargs: Any) -> List[AIMessage]:
    """Collect every chunk emitted by :meth:`LLMAdapter.astream`."""

    return [chunk async for chunk in adapter.astream(messages, **kwargs)]


async def async_iter(items: List[AIMessage]) -> AsyncIterable[AIMessage]:
    """Yield provided chunks to emulate an async LLM stream."""
    for item in items:
        yield item
