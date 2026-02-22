"""
Adapter for LangChain LLMs.
"""

from typing import Any, AsyncIterable, Dict, List, Protocol

import instructor
from json_repair import repair_json
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import BaseTool

from src.configs.consts import INSTRUCTOR_ROLE_MAP
from src.configs.log.logger import get_logger
from src.schemas.base import Schema


class LLMProtocol(Protocol):
    """Minimal protocol that LLMAdapter requires from a LLM chat model."""

    model_name: str
    async_client: Any

    async def ainvoke(self, messages: List[BaseMessage], **kwargs: Any) -> Any: ...

    def astream(self, messages: List[BaseMessage], **kwargs: Any) -> AsyncIterable[AIMessage]: ...

    def bind_tools(self, tools: List[BaseTool | Dict[str, Any]], **kwargs: Any) -> "LLMProtocol": ...  # noqa: WPS221

    def with_config(self, config: Dict[str, Any]) -> "LLMProtocol": ...

    def with_structured_output(
        self,
        schema: type[Schema],
        include_raw: bool = False,
        method: str = "json_mode",
    ) -> "LLMProtocol": ...


class LLMAdapter:
    """Thin wrapper around a LangChain chat model providing a stable, typed API.

    Adds structured output with guaranteed retries on top of the standard
    LangChain interface. When the underlying model exposes an async OpenAI
    client (i.e. ChatOpenAI), the Instructor library is used for structured
    invocation. Otherwise the adapter falls back to a manual retry loop built
    on LangChain's with_structured_output.

    Parameters
    ----------
    llm
        Any object that satisfies LLMProtocol. In production this is
        typically a ChatOpenAI instance.
    """

    def __init__(self, llm: LLMProtocol) -> None:
        self._llm: LLMProtocol = llm
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._instructor_client = self._setup_instructor_client()

    @staticmethod
    def to_openai_message(message: BaseMessage) -> dict[str, str]:
        role = INSTRUCTOR_ROLE_MAP.get(message.type, message.type)
        return {"role": role, "content": message.content}

    async def ainvoke(self, messages: List[BaseMessage], **kwargs: Any) -> str:
        """Invoke the LLM and return the generated text as a plain string.

        Parameters
        ----------
        messages
            Conversation history to pass to the model.
        **kwargs
            Extra arguments forwarded directly to the underlying LLM.

        Raises
        ------
        RuntimeError
            Wraps any exception raised by the underlying LLM call.
        """
        try:
            response: AIMessage = await self._llm.ainvoke(messages, **kwargs)
        except Exception as exc:
            self._logger.error(f"LLM invocation error: {exc}")
            raise RuntimeError(f"Failed to invoke LLM: {exc}") from exc
        return response.content

    async def astream(self, messages: List[BaseMessage], **kwargs: Any) -> AsyncIterable[AIMessage]:
        """Stream AIMessage chunks from the LLM.

        Parameters
        ----------
        messages
            Conversation history to pass to the model.
        **kwargs
            Extra arguments forwarded directly to the underlying LLM.

        Yields
        ------
        AIMessage
            Successive chunks produced by the model during streaming.

        Raises
        ------
        RuntimeError
            Wraps any exception raised during the streaming call.
        """
        try:
            async for chunk in await self._llm.astream(messages, **kwargs):
                yield chunk
        except Exception as exc:
            self._logger.error(f"LLM streaming error: {exc}")
            raise RuntimeError(f"Failed to stream from LLM: {exc}") from exc

    def bind_tools(self, tools: List[BaseTool | Dict[str, Any]], **kwargs: Any) -> "LLMAdapter":
        """Return a new adapter with the given tools bound to the underlying LLM.

        Does not mutate the current instance. A fresh LLMAdapter is created
        around the bound LLM, which keeps state reasoning simple.

        Parameters
        ----------
        tools
            LangChain BaseTool instances or plain tool-schema dicts to bind.
        **kwargs
            Extra arguments forwarded to the underlying bind_tools call.

        Raises
        ------
        RuntimeError
            Wraps any exception raised during tool binding.
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
        """Bind tools, invoke the LLM, and return the generated text.

        Combines bind_tools and ainvoke into a single convenience call.
        The return type is a plain string, same as ainvoke.

        Parameters
        ----------
        messages
            Conversation history to pass to the model.
        tools
            Tools to bind before invoking.
        **kwargs
            Extra arguments forwarded to the underlying LLM.
        """
        bound_adapter = self.bind_tools(tools)
        return await bound_adapter.ainvoke(messages, **kwargs)

    def with_config(self, config: Dict[str, Any]) -> "LLMAdapter":
        """Return a new adapter with an updated LLM configuration.

        Does not mutate the current instance. Typical keys include
        temperature and max_tokens.

        Parameters
        ----------
        config
            Configuration dict passed to the underlying LLM's with_config.

        Raises
        ------
        RuntimeError
            Wraps any exception raised during reconfiguration.
        """
        try:
            updated_llm = self._llm.with_config(config)
        except Exception as exc:
            self._logger.error(f"LLM config update error: {exc}")
            raise RuntimeError(f"Failed to update LLM config: {exc}") from exc
        return LLMAdapter(updated_llm)

    async def structured_ainvoke(
        self,
        messages: List[BaseMessage],
        schema: type[Schema],
        max_retries: int = 3,
        **kwargs: Any,
    ) -> Schema:
        """Invoke the LLM and return a validated instance of schema.

        Tries Instructor first when available, then falls back to the manual
        LangChain retry loop. Both paths retry up to max_retries times and
        send the validation error back to the model as feedback on each failed
        attempt, which significantly increases the success rate compared to a
        plain single-shot call.

        Parameters
        ----------
        messages
            Conversation history to pass to the model.
        schema
            A Pydantic BaseModel subclass describing the expected output shape.
        max_retries
            Maximum number of attempts before raising RuntimeError.
        **kwargs
            Extra arguments forwarded to the underlying LLM call.

        Raises
        ------
        RuntimeError
            Raised when all retry attempts are exhausted without a valid result.
        """
        if not self._instructor_client:
            self._logger.warning("Instructor client not available, falling back to base structured invoke.")
            return await self._base_structured_ainvoke(messages, schema, max_retries, **kwargs)

        openai_messages = [self.to_openai_message(message) for message in messages]
        return await self._instructor_client.chat.completions.create(
            model=self._llm.model_name,
            response_model=schema,
            messages=openai_messages,
            max_retries=max_retries,
        )

    def _setup_instructor_client(self) -> instructor.AsyncInstructor | None:
        """Extract the underlying async OpenAI client and wrap it with Instructor.

        Returns None when the LLM does not expose an async_client attribute,
        which triggers the LangChain fallback path in structured_ainvoke.
        """
        try:
            return instructor.from_openai(self._llm.async_client)
        except (AttributeError, Exception) as exc:
            self._logger.warning(f"Could not initialize Instructor: {exc}")
            return None

    def _try_repair_json(self, raw_content: str, schema: type[Schema]) -> Schema | None:
        """Try to fix malformed JSON with json-repair and validate it against schema.

        Returns a validated schema instance on success, or None if repair fails.
        """
        try:
            fixed_json = repair_json(raw_content)
        except Exception as repair_exc:
            self._logger.debug(f"json-repair failed: {repair_exc}")
            return None

        try:
            return schema.model_validate_json(fixed_json)
        except Exception as repair_exc:
            self._logger.debug(f"json-repair failed: {repair_exc}")
            return None

    def _build_feedback_messages(
        self,
        current_messages: List[BaseMessage],
        raw_content: str,
        parsing_error: Exception | None,
    ) -> List[BaseMessage]:
        """Append the model's invalid output and a correction prompt to the conversation."""
        return [
            *current_messages,
            AIMessage(content=raw_content or ""),
            HumanMessage(
                content=(
                    f"Your previous response caused a validation error: {parsing_error}. "
                    f"You MUST respond with valid JSON strictly matching the schema. "
                    f"Do not add any explanation outside the JSON object."
                ),
            ),
        ]

    def _handle_parse_failure(
        self,
        response: Schema,
        current_messages: List[BaseMessage],
        attempt: int,
        max_retries: int,
        schema: type[Schema],
    ) -> tuple[Schema | None, List[BaseMessage]]:
        """Handle a failed parse attempt.

        Tries json-repair first. If that fails, builds feedback messages for
        the next LLM retry. Returns a tuple of (repaired_result_or_None, updated_messages).
        """
        parsing_error = response.get("parsing_error")
        raw = response.get("raw")
        raw_content: str = raw.content if raw else ""

        self._logger.warning(f"Attempt {attempt}/{max_retries}: parsing error: {parsing_error}")

        if raw_content:
            repaired = self._try_repair_json(raw_content, schema)
            if repaired:
                return repaired, current_messages

        updated_messages = self._build_feedback_messages(current_messages, raw_content, parsing_error)
        return None, updated_messages

    async def _base_structured_ainvoke(
        self,
        messages: List[BaseMessage],
        schema: type[Schema],
        max_retries: int = 3,
        **kwargs: Any,
    ) -> Schema:
        """Structured invocation fallback using LangChain's with_structured_output.

        On each failed parse attempt the raw invalid output and the validation
        error message are appended to the conversation so the model can
        self-correct on the next try. Before retrying the LLM, json-repair is
        attempted on the raw output as a cheaper recovery path.

        Parameters
        ----------
        messages
            Conversation history to pass to the model.
        schema
            A Pydantic BaseModel subclass describing the expected output shape.
        max_retries
            Maximum number of attempts before raising RuntimeError.
        **kwargs
            Extra arguments forwarded to the underlying LLM.

        Raises
        ------
        RuntimeError
            Raised when all retry attempts are exhausted without a valid result.
        """
        current_messages = list(messages)
        last_exc: Exception | None = None
        structured_llm = self._llm.with_structured_output(schema, include_raw=True, method="json_mode")

        for attempt in range(1, max_retries + 1):
            response, exc = await self._safe_invoke(structured_llm, current_messages, **kwargs)

            if exc:
                last_exc = exc
                self._logger.error(f"Attempt {attempt}/{max_retries} unexpected error: {exc}")
            elif response.get("parsed"):
                return response["parsed"]
            else:
                handle_result, current_messages = self._handle_parse_failure(
                    response,
                    current_messages,
                    attempt,
                    max_retries,
                    schema,
                )
                if handle_result:
                    return handle_result

        raise RuntimeError(
            f"Failed to get structured output after {max_retries} attempts. Last error: {last_exc}",
        )

    @staticmethod
    async def _safe_invoke(
        structured_llm: LLMProtocol,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> tuple[Schema, Exception | None]:
        """Invoke the structured LLM and return (response, error).

        Never raises — exceptions are returned as the second tuple element
        so the retry loop can stay flat without nested try blocks.
        """
        try:
            return await structured_llm.ainvoke(messages, **kwargs), None
        except Exception as exc:
            return {}, exc
