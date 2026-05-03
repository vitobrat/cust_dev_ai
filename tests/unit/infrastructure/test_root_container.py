"""Unit tests validating the root dependency injection container."""

from __future__ import annotations

from unittest.mock import MagicMock

from langfuse.langchain import CallbackHandler

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.final_report_generation import (
    FinalReportGenerationGraph,
)
from src.domains.interview.infrastructure.graph.interview_orchestrator import (
    InterviewOrchestratorGraph,
)
from src.domains.interview.infrastructure.graph.interview_simulation import (
    InterviewSimulationGraph,
)
from src.domains.interview.infrastructure.graph.post_interview_update import (
    PostInterviewUpdateGraph,
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
        container.interview.interviews_repository.override(MagicMock()),  # type: ignore[attr-defined]
        container.interview.sub_interviews_repository.override(MagicMock()),  # type: ignore[attr-defined]
    ):
        prompt_builder = container.interview.prompt_builder()
        pre_interview_graph = container.interview.pre_interview_preparation_graph()
        simulation_graph = container.interview.interview_simulation_graph()
        post_interview_graph = container.interview.post_interview_update_graph()
        orchestrator_graph = container.interview.interview_orchestrator_graph()
        final_report_graph = container.interview.final_report_generation_graph()
        task_handler = container.interview.interview_simulation_task_handler()

    assert isinstance(prompt_builder, InterviewPromptManager)
    assert isinstance(pre_interview_graph, PreInterviewPreparationGraph)
    assert isinstance(simulation_graph, InterviewSimulationGraph)
    assert isinstance(post_interview_graph, PostInterviewUpdateGraph)
    assert isinstance(orchestrator_graph, InterviewOrchestratorGraph)
    assert isinstance(final_report_graph, FinalReportGenerationGraph)
    assert (
        pre_interview_graph._prompt_builder,
        simulation_graph._prompt_builder,
        post_interview_graph._prompt_builder,
        final_report_graph._prompt_builder,
    ) == (prompt_builder, prompt_builder, prompt_builder, prompt_builder)
    assert task_handler._interview_service is not None
