"""Unit tests for LLM infrastructure configuration."""

from langchain_openai import ChatOpenAI

from src.configs.infrastructure_config import LLMConfigs
from src.infrastructure.containers.infrastructure import InfrastructureContainer


def test_llm_config_disables_reasoning_by_default() -> None:
    """Disabled reasoning should send an explicit OpenRouter no-reasoning payload."""
    configs = LLMConfigs(
        model_name="qwen/qwen3.5-27b",
        base_url="https://openrouter.ai/api/v1",
        LLM_API_KEY="test-key",
        temperature=0.1,
        max_tokens=4096,
    )

    assert configs.extra_body_payload == {
        "reasoning": {
            "effort": "none",
            "exclude": True,
        },
    }


def test_llm_config_merges_enabled_reasoning_with_provider_extra_body() -> None:
    """Enabled reasoning should compose with provider-specific extra_body values."""
    configs = LLMConfigs(
        model_name="qwen/qwen3.5-27b",
        base_url="https://openrouter.ai/api/v1",
        LLM_API_KEY="test-key",
        temperature=0.1,
        max_tokens=4096,
        reasoning={
            "enabled": True,
            "effort": "high",
            "exclude": True,
        },
        extra_body={
            "enable_thinking": False,
        },
    )

    assert configs.extra_body_payload == {
        "reasoning": {
            "effort": "high",
            "exclude": True,
        },
        "enable_thinking": False,
    }


def test_infrastructure_container_passes_llm_extra_body_to_chat_openai() -> None:
    """The DI container should pass computed provider payload through ChatOpenAI.extra_body."""
    container = InfrastructureContainer()
    container.config.from_dict(
        {
            "llm": {
                "model_name": "qwen/qwen3.5-27b",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "test-key",
                "temperature": 0.1,
                "max_tokens": 4096,
                "extra_body_payload": {
                    "reasoning": {
                        "effort": "none",
                        "exclude": True,
                    },
                },
            },
        },
    )

    llm = container.llm()

    assert isinstance(llm, ChatOpenAI)
    assert llm.extra_body == {
        "reasoning": {
            "effort": "none",
            "exclude": True,
        },
    }
