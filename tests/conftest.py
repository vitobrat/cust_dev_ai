"""Pytest fixtures and configuration for the project."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMProtocol


@pytest.fixture(scope='session')
def container() -> RootContainer:
    """Fixture providing a configured RootContainer instance."""
    container = RootContainer()
    container.wire(modules=[__name__])
    return container


@pytest.fixture
def mock_llm() -> LLMProtocol:
    """Fixture providing a spec-based LLM mock instance."""
    llm_mock = MagicMock(spec_set=LLMProtocol)
    llm_mock.ainvoke = AsyncMock()
    llm_mock.astream = AsyncMock()
    llm_mock.bind_tools = MagicMock(return_value=llm_mock)
    llm_mock.with_config = MagicMock(return_value=llm_mock)
    llm_mock.with_structured_output = MagicMock(return_value=llm_mock)
    return cast(LLMProtocol, llm_mock)


@pytest.fixture(autouse=True)
def override_llm_adapter(container: RootContainer, mock_llm: LLMProtocol):
    """Automatically override the LLMAdapter dependency with a mock."""
    with container.llm_adapter.override(mock_llm):
        yield
