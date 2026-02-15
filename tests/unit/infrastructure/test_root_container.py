"""Unit tests validating the root dependency injection container."""

from __future__ import annotations

from unittest.mock import MagicMock

from langfuse.langchain import CallbackHandler

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
