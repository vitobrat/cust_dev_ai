"""Unit tests validating the root dependency injection container."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from tests.unit.infrastructure.consts import LLM_CONFIG
from tests.unit.infrastructure.utils import configured_root_container


def test_root_container_wires_llm_and_adapter() -> None:
    """Ensure the container resolves both the LLM and its adapter."""

    container = configured_root_container()
    with patch.object(ChatOpenAI, "__init__", return_value=None):
        llm_instance = container.infrastructure.llm()
        llm_adapter = container.infrastructure.llm_adapter()

    assert isinstance(llm_instance, ChatOpenAI)
    assert llm_adapter._llm is llm_instance


def test_root_container_applies_llm_configuration() -> None:
    """Verify the ChatOpenAI constructor receives the configured values."""

    container = configured_root_container()
    with patch.object(ChatOpenAI, "__init__", return_value=None) as init_mock:
        container.infrastructure.llm()

    assert init_mock.call_count == 1
    call_kwargs = init_mock.call_args.kwargs
    assert call_kwargs["model_name"] == LLM_CONFIG["model_name"]
    assert call_kwargs["api_key"] == LLM_CONFIG["api_key"]
    assert call_kwargs["temperature"] == LLM_CONFIG["temperature"]
    assert call_kwargs["max_tokens"] == LLM_CONFIG["max_tokens"]
    assert call_kwargs["base_url"] == LLM_CONFIG["base_llm_url"]

    
def test_root_container_exposes_langfuse_client_and_handler() -> None:
    """Ensure Langfuse client and handler bindings are available."""

    container = configured_root_container()
    fake_client = MagicMock()
    fake_handler = MagicMock(spec=CallbackHandler)

    with (
        patch(
            'src.infrastructure.containers.root.get_client',
            return_value=fake_client,
        ) as client_factory,
        patch(
            'src.infrastructure.containers.root.CallbackHandler',
            return_value=fake_handler,
        ) as handler_factory,
    ):
        client_instance = container.langfuse_client()
        handler_instance = container.langfuse_handler()

    assert client_instance is fake_client
    client_factory.assert_called_once()
    handler_factory.assert_called_once()
    assert handler_instance is fake_handler
