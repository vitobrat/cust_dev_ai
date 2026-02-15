"""Pytest fixtures and configuration for the project."""

from typing import Any, Generator, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMAdapter, LLMProtocol
from tests.schema import DummyOutputSchema


@pytest.fixture(scope="session")
def container() -> RootContainer:
    """Fixture providing a configured RootContainer instance."""
    container = RootContainer()
    container.wire(modules=["tests"])
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
def override_llm(container: RootContainer, mock_llm: LLMProtocol) -> Generator[Any, Any, Any]:
    """Automatically override the LLM dependency with a mock."""
    with container.infrastructure.llm.override(mock_llm):
        yield


@pytest.fixture
def mock_llm_adapter() -> LLMAdapter:
    """Construct an LLMAdapter using the shared mock llm."""
    llm_adapter_mock = MagicMock(spec=LLMAdapter)
    llm_adapter_mock.ainvoke = AsyncMock(return_value="llm adapter ainvoke")
    llm_adapter_mock.structured_ainvoke = AsyncMock(
        return_value=DummyOutputSchema(output="llm adapter structuted output"),
    )

    return cast(LLMAdapter, llm_adapter_mock)
