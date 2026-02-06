from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any, List

from langchain_core.messages import AIMessage, BaseMessage
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from tests.unit.infrastructure.base_graph.graph_mock import MockBaseGraph
from tests.unit.infrastructure.consts import LLM_CONFIG


def configured_root_container() -> RootContainer:
    """Return a RootContainer with llm configuration applied."""

    container = RootContainer()
    container.config.from_dict({'llm': dict(LLM_CONFIG)})
    return container


def make_graph(
    compiled_graph: CompiledStateGraph,
    test_schemas: tuple[type[BaseModel], type[BaseModel]],
    llm_adapter: LLMAdapter,
    prompt_builder: BasePromptManager,
    *,
    recursion_limit: int | None = None,
    langfuse_handler: CallbackHandler | None = None,
) -> MockBaseGraph:
    state_schema, output_schema = test_schemas
    return MockBaseGraph(
        state_schema=state_schema,
        output_schema=output_schema,
        llm_adapter=llm_adapter,
        prompt_builder=prompt_builder,
        compiled_graph=compiled_graph,
        recursion_limit=recursion_limit,
        langfuse_handler=langfuse_handler,
    )


async def collect_stream(adapter: LLMAdapter, messages: List[BaseMessage], **kwargs: Any) -> List[AIMessage]:
    """Collect every chunk emitted by :meth:`LLMAdapter.astream`."""

    return [chunk async for chunk in adapter.astream(messages, **kwargs)]


async def async_iter(items: List[AIMessage]) -> AsyncIterable[AIMessage]:
    """Yield provided chunks to emulate an async LLM stream."""
    for item in items:
        yield item
