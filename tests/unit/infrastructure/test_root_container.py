"""Unit tests validating the root dependency injection container."""

from __future__ import annotations

from unittest.mock import MagicMock

from langfuse.langchain import CallbackHandler

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.interview_simulation import (
    InterviewSimulationGraph,
)
from src.domains.interview.infrastructure.graph.pre_interview_preparation import (
    PreInterviewPreparationGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.infrastructure.containers.domain import DomainContainer
from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMAdapter, LLMProtocol


def test_root_container_wires_llm_and_adapter(container: RootContainer, mock_llm: LLMProtocol) -> None:
    """Ensure the container resolves both the LLM and its adapter."""
    llm_instance = container.infrastructure.llm()
    adapter_instance: LLMAdapter = container.infrastructure.llm_adapter()

    assert isinstance(adapter_instance, LLMAdapter)

    assert adapter_instance._llm is llm_instance
    assert adapter_instance._llm is mock_llm


def test_root_container_exposes_langfuse_client_and_handler(container: RootContainer) -> None:
    """Ensure Langfuse client and handler bindings are available."""
    fake_client = MagicMock()
    fake_handler = MagicMock(spec=CallbackHandler)

    with (
        container.infrastructure.langfuse_client.override(fake_client),
        container.infrastructure.langfuse_handler.override(fake_handler),
    ):
        client_instance = container.infrastructure.langfuse_client()
        handler_instance = container.infrastructure.langfuse_handler()

        assert client_instance is fake_client
        assert handler_instance is fake_handler

    real_client = container.infrastructure.langfuse_client()
    real_handler = container.infrastructure.langfuse_handler()

    assert real_client is not fake_client
    assert isinstance(real_handler, CallbackHandler)


def test_interview_container_exposes_pre_interview_preparation_graph(mock_llm: LLMProtocol) -> None:
    """Ensure the interview domain resolves its first-stage graph dependencies."""
    container = DomainContainer()
    container.config.from_dict(
        {
            "interview": {
                "prompts_dir": PROJECT_ROOT / "src/domains/interview/infrastructure/prompt",
                "recursion_limit": 10,
                "simulation_recursion_limit": 80,
            },
        },
    )
    fake_handler = MagicMock(spec=CallbackHandler)

    with (
        container.infrastructure.llm.override(mock_llm),
        container.infrastructure.langfuse_handler.override(fake_handler),
    ):
        prompt_builder = container.interview.prompt_builder()
        pre_interview_graph = container.interview.pre_interview_preparation_graph()
        simulation_graph = container.interview.interview_simulation_graph()

    assert isinstance(prompt_builder, InterviewPromptManager)
    assert isinstance(pre_interview_graph, PreInterviewPreparationGraph)
    assert isinstance(simulation_graph, InterviewSimulationGraph)
    assert pre_interview_graph._prompt_builder is prompt_builder
    assert simulation_graph._prompt_builder is prompt_builder
