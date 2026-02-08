"""
Adapter for LangChain LLMs.
"""

from typing import Any, AsyncIterable, Dict, List, Protocol

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from src.configs.log.logger import get_logger
from src.schemas.base import Schema


class LLMProtocol(Protocol):
    """Minimal protocol required by :class:`LLMAdapter`.

    Only the methods used by the adapter are declared.  Concrete LLM classes
    such as :class:`ChatOpenAI` automatically satisfy this protocol.
    """

    async def ainvoke(self, messages: List[BaseMessage], **kwargs: Any) -> Any: ...

    def astream(self, messages: List[BaseMessage], **kwargs: Any) -> AsyncIterable[AIMessage]: ...

    def bind_tools(self, tools: List[BaseTool | Dict[str, Any]], **kwargs: Any) -> 'LLMProtocol': ...  # noqa: WPS221

    def with_config(self, config: Dict[str, Any]) -> 'LLMProtocol': ...

    def with_structured_output(
        self,
        schema: type[Schema],
        include_raw: bool = False,
        method: str = 'json_mode',
    ) -> 'LLMProtocol': ...


class LLMAdapter:
    """Thin wrapper around a LangChain LLM providing a stable, typed API.

    Parameters
    ----------
    llm:
        An instance that conforms to :class:`LLMProtocol`.  In production this
        will typically be :class:`ChatOpenAI`.
    """

    def __init__(self, llm: LLMProtocol) -> None:
        self._llm: LLMProtocol = llm
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    async def ainvoke(self, messages: List[BaseMessage], **kwargs: Any) -> str:
        """Asynchronously invoke the LLM and return the generated text.

        The underlying LLM is expected to return an object with a ``content``
        attribute (e.g., :class:`AIMessage`).  If the call fails, the error is
        logged and a ``RuntimeError`` is raised.
        """
        try:
            response: AIMessage = await self._llm.ainvoke(messages, **kwargs)
        except Exception as exc:
            self._logger.error(f"LLM invocation error: {exc}")
            raise RuntimeError(f"Failed to invoke LLM: {exc}") from exc
        return response.content

    async def astream(self, messages: List[BaseMessage], **kwargs: Any) -> AsyncIterable[AIMessage]:
        """Yield streamed ``AIMessage`` objects from the LLM.

        Errors are logged and re‑raised as ``RuntimeError`` to keep the public
        API consistent.
        """
        try:
            async for chunk in await self._llm.astream(messages, **kwargs):
                yield chunk
        except Exception as exc:
            self._logger.error(f"LLM streaming error: {exc}")
            raise RuntimeError(f"Failed to stream from LLM: {exc}") from exc

    def bind_tools(self, tools: List[BaseTool | Dict[str, Any]], **kwargs: Any) -> 'LLMAdapter':
        """Return a new adapter with ``tools`` bound to the underlying LLM.

        The method does not mutate the current instance; instead it creates a
        fresh :class:`LLMAdapter` wrapping the bound LLM.  This functional style
        simplifies reasoning about state.
        """
        try:
            bound_llm = self._llm.bind_tools(tools, **kwargs)
        except Exception as exc:
            self._logger.error(f"Tool binding error: {exc}")
            raise RuntimeError(f"Failed to bind tools: {exc}") from exc
        return LLMAdapter(bound_llm)

    async def ainvoke_with_tools(
        self,
        messages: List[BaseMessage],
        tools: List[BaseTool | Dict[str, Any]],
        **kwargs: Any,
    ) -> str:
        """Invoke the LLM after binding ``tools``.

        The return type mirrors :meth:`ainvoke` – a plain string containing the
        generated content.
        """
        bound_adapter = self.bind_tools(tools)
        bound_adapter_response: AIMessage = await bound_adapter.ainvoke(messages, **kwargs)
        return bound_adapter_response.content

    def with_config(self, config: Dict[str, Any]) -> 'LLMAdapter':
        """Return a new adapter with an updated LLM configuration.

        Typical configuration keys include ``temperature`` or ``max_tokens``.
        """
        try:
            updated_llm = self._llm.with_config(config)
        except Exception as exc:  # pragma: no cover – exercised via tests
            self._logger.error(f"LLM config update error: {exc}")
            raise RuntimeError(f"Failed to update LLM config: {exc}") from exc
        return LLMAdapter(updated_llm)

    async def structured_ainvoke(
        self,
        messages: List[BaseMessage],
        schema: type[Schema],
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Schema:
        """Invoke the LLM with a structured output schema.

        Parameters
        ----------
        messages:
            Conversation history passed to the model.
        schema:
            A ``pydantic.BaseModel`` subclass or ``TypedDict`` describing the
            expected JSON structure.
        include_raw:
            If ``True`` the raw model response (including potential parsing
            errors) is returned alongside the parsed object.
        **kwargs:
            Additional arguments forwarded to the underlying LLM.
        """
        try:
            structured_llm = self._llm.with_structured_output(
                schema,
                include_raw=include_raw,
                method='json_mode',
            )
        except AttributeError as exc:
            self._logger.error(f"Structured output setup error: {exc}")
            raise RuntimeError(f"LLM does not support structured output: {exc}") from exc
        except Exception as exc:
            self._logger.error(f"Structured output setup error: {exc}")
            raise RuntimeError(f"Failed to set up structured output: {exc}") from exc

        try:
            response = await structured_llm.ainvoke(messages, **kwargs)
        except Exception as exc:  # pragma: no cover – exercised via tests
            self._logger.error(f"Structured LLM invocation error: {exc}")
            raise RuntimeError(f"Failed to invoke structured LLM: {exc}") from exc
        if include_raw and isinstance(response, dict) and response.get('parsing_error'):
            self._logger.warning(
                f"Parsing error in structured output: {response['parsing_error']}",
            )
        return response
