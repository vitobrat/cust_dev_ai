"""Base graph implementation for LangGraph agents.

This module provides an abstract base class for building LangGraph-based agents
with standardized configuration, error handling, and execution patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.configs.consts import DEFAULT_GRAPH_RECURSION_LIMIT
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager
from src.schemas.base import Schema


class GraphError(Exception):
    """Base exception for graph-related errors."""


class BaseGraph(StateGraph, ABC):
    """Abstract base class for LangGraph-based agents.

    This class provides a standardized way to build, configure, and execute
    LangGraph state machines with integrated LLM adapters, prompt management,
    and observability through Langfuse.

    Subclasses must implement :meth:`_configurate_graph` to define the graph
    structure (nodes and edges).

    Args:
        state_schema: Pydantic model or TypedDict defining the graph state.
        output_schema: Pydantic model or TypedDict for the output structure.
        llm_adapter: Adapter wrapping the LLM for standardized invocation.
        prompt_builder: Manager for loading and building prompt templates.
        recursion_limit: Maximum recursion depth for graph execution.
        langfuse_handler: Optional callback handler for Langfuse tracing.

    Attributes:
        _llm_adapter: The LLM adapter instance.
        _prompt_builder: The prompt manager instance.
        _langfuse_handler: Optional Langfuse callback handler.
        _recursion_limit: Maximum recursion depth.
        _graph: Compiled state graph ready for execution.
        output_schema: Schema class for output validation.
    """

    def __init__(
        self,
        state_schema: Schema,
        llm_adapter: LLMAdapter,
        prompt_builder: BasePromptManager,
        output_schema: Optional[Schema] = None,
        recursion_limit: int = DEFAULT_GRAPH_RECURSION_LIMIT,
        langfuse_handler: Optional[CallbackHandler] = None,
    ) -> None:
        """Initialize the base graph with configuration and dependencies."""
        super().__init__(state_schema, output_schema=output_schema)
        self._llm_adapter: LLMAdapter = llm_adapter
        self._prompt_builder: BasePromptManager = prompt_builder
        self._langfuse_handler: Optional[CallbackHandler] = langfuse_handler
        self._recursion_limit: int = recursion_limit
        self.output_schema: Schema = output_schema
        self.graph: CompiledStateGraph = self._build_graph()

    async def process(
        self,
        state: Schema,
    ) -> Schema:
        """Execute the graph with the given state.

        Args:
            state: Initial state dictionary conforming to the state schema.

        Returns:
            Output instance conforming to the output schema.

        Raises:
            GraphError: If the graph execution fails or returns None.
        """
        graph_process_configs: Dict[str, Any] = {
            "recursion_limit": self._recursion_limit,
        }
        if self._langfuse_handler:
            graph_process_configs["callbacks"] = [self._langfuse_handler]

        try:
            graph_result = await self.graph.ainvoke(
                state,
                config=graph_process_configs,
            )
        except Exception as exc:
            raise GraphError(
                f"Error during {self.__class__.__name__} execution: {exc}",
            ) from exc

        if graph_result is None:
            raise GraphError(
                f"Graph {self.__class__.__name__} returned None response",
            )

        try:
            return self.output_schema(**graph_result)
        except Exception as exc:
            raise GraphError(
                f"Failed to validate output for {self.__class__.__name__}: {exc}",
            ) from exc

    def _build_graph(self) -> CompiledStateGraph:
        """Build and compile the graph.

        This method calls :meth:`_configurate_graph` to set up the graph
        structure and then compiles it into an executable state machine.

        Returns:
            Compiled state graph ready for execution.
        """
        self._configurate_graph()
        return self.compile()

    @abstractmethod
    def _configurate_graph(self) -> None:
        """Configure the graph structure by adding nodes and edges.

        Subclasses must implement this method to define the graph topology.
        Use :meth:`add_node` and :meth:`add_edge` to build the graph structure.

        Example:
            def _configurate_graph(self) -> None:
                self.add_node("process", self._process_node)
                self.add_edge(START, "process")
                self.add_edge("process", END)
        """
