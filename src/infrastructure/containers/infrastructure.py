from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

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

    llm_adapter: LLMAdapter = providers.Factory(
        LLMAdapter,
        llm=llm,
    )

    langfuse_client = providers.Singleton(get_client)

    langfuse_handler = providers.Factory(CallbackHandler)
