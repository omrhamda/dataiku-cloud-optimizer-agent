"""
LLM engine wrapper used by the agent for summarization and reasoning.
"""

from typing import Any, Callable, Dict, Optional, TYPE_CHECKING  # noqa: I001

try:  # pragma: no cover
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency during tests
    OpenAI = None  # type: ignore

if TYPE_CHECKING:  # For static type checking only
    from openai import OpenAI as OpenAIType
else:  # Runtime fallback
    OpenAIType = Any


class LLMEngine:
    """Thin wrapper around OpenAI client with a summarize() helper."""

    def __init__(
        self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"
    ) -> None:
        self.model = model
        self.enabled = OpenAI is not None and api_key is not None
        self._client: Optional[OpenAIType] = (
            OpenAI(api_key=api_key) if self.enabled else None
        )

    def summarize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        if not self.enabled or self._client is None:
            return text

        system_prompt = "You are an assistant that writes clear, concise executive summaries of cloud optimization recommendations."
        user_content = (
            "Summarize the following findings for a business audience. Include estimated savings and clear next steps.\n\n"
            + text
        )
        if context:
            user_content += "\n\nContext:" + str(context)

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            return resp.choices[0].message.content or text
        except Exception:
            # Fail open – return original text
            return text


class CallbackLLMEngine:
    """LLM engine that delegates to a user-provided callable.

    Useful inside Dataiku DSS to invoke LLM Mesh via the official Python API
    without hard-coding SDK calls here. The callback signature should be:
        fn(prompt: str, context: Optional[Dict[str, Any]]) -> str
    """

    def __init__(self, fn: Callable[[str, Optional[Dict[str, Any]]], str]):
        self._fn: Callable[[str, Optional[Dict[str, Any]]], str] = fn

    def summarize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            return self._fn(text, context)
        except Exception:
            return text
