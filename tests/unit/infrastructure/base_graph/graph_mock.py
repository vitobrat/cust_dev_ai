from __future__ import annotations

from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager


class MockBaseGraph(BaseGraph):
    """Minimal graph implementation used for BaseGraph unit tests."""

    _compiled_graph: CompiledStateGraph
    configured: bool

    def __init__(
        self,
        state_schema: type[BaseModel],
        output_schema: type[BaseModel],
        llm_adapter: LLMAdapter,
        prompt_builder: BasePromptManager,
        compiled_graph: CompiledStateGraph,
        recursion_limit: int | None = None,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        self._compiled_graph = compiled_graph
        self.configured = False
        super().__init__(
            state_schema=state_schema,
            output_schema=output_schema,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        """Track that configuration ran without needing actual nodes."""

        self.configured = True

    def compile(self) -> CompiledStateGraph:
        """Return the prepared compiled graph instead of computing a new one."""

        return self._compiled_graph
