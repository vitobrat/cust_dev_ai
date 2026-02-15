from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any, List

from langchain_core.messages import AIMessage, BaseMessage

from src.infrastructure.llm.llm_adapter import LLMAdapter


async def collect_stream(adapter: LLMAdapter, messages: List[BaseMessage], **kwargs: Any) -> List[AIMessage]:
    """Collect every chunk emitted by :meth:`LLMAdapter.astream`."""

    return [chunk async for chunk in adapter.astream(messages, **kwargs)]


async def async_iter(iter_items: List[AIMessage]) -> AsyncIterable[AIMessage]:
    """Yield provided chunks to emulate an async LLM stream."""
    for iter_item in iter_items:
        yield iter_item
