from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI

from src.configs.config import AppConfigs
from src.infrastructure.llm.llm_adapter import LLMAdapter


class InfrastructureContainer(containers.DeclarativeContainer):
    config: AppConfigs = providers.Configuration()

    llm: ChatOpenAI = providers.Singleton(
        ChatOpenAI,
        model_name=config.llm.model_name,
        api_key=config.llm.api_key,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        base_url=config.llm.base_llm_url,
    )

    llm_adapter: LLMAdapter = providers.Singleton(
        LLMAdapter,
        llm=llm,
    )
