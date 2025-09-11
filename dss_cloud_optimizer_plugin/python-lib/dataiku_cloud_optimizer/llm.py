"""Very small LLM wrapper stub for summarization inside DSS.

Supports either:
1. A DSS LLM Mesh connection name (preferred) -> uses dataikuapi LLM interface
2. Direct OpenAI-style API key fallback.

Falls back to returning the base summary on any error.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import os

class SimpleLLM:
    def __init__(self, api_key: Optional[str], model: str = "gpt-4o-mini", max_tokens: int = 512, llm_connection: Optional[str] = None) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.llm_connection = llm_connection
        self._client = None  # lazy (OpenAI) or DSS mesh handle
        self._mesh = None    # DSS LLM mesh client

    def _ensure_mesh(self) -> None:
        if self.llm_connection and self._mesh is None:
            try:  # pragma: no cover - depends on DSS runtime
                import dataiku  # type: ignore

                self._mesh = dataiku.llm.get_llm(self.llm_connection)
            except Exception:
                self._mesh = None

    def _ensure_client(self) -> None:
        if self.api_key and self._client is None:
            try:  # pragma: no cover - optional dependency
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    def summarize(self, base_summary: str, context: Dict[str, Any]) -> str:
        # Prefer DSS LLM Mesh
        if self.llm_connection:
            self._ensure_mesh()
            if self._mesh is None:
                return base_summary
            try:  # pragma: no cover
                prompt = (
                    "You are a FinOps assistant. Using the JSON context below, produce a concise, executive "
                    "summary (<= 120 words) focusing on total savings and top opportunities.\nContext:\n"
                    + json.dumps(context) + "\nBase Summary:\n" + base_summary
                )
                result = self._mesh.run(prompt, purpose="GENERIC_COMPLETION")
                # result may be dict or object depending on DSS; try common fields
                if isinstance(result, dict):
                    return result.get("text") or result.get("answer") or base_summary
                return getattr(result, "text", base_summary) or base_summary
            except Exception:
                return base_summary

        # Fallback to direct OpenAI key
        if not self.api_key:
            return base_summary
        self._ensure_client()
        if self._client is None:
            return base_summary
        try:  # pragma: no cover
            prompt = (
                "You are a FinOps assistant. Using the JSON context below, produce a concise, executive "
                "summary (<= 120 words) focusing on total savings and top opportunities.\nContext:\n"
                + json.dumps(context) + "\nBase Summary:\n" + base_summary
            )
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=0.2,
            )
            choice = resp.choices[0]
            return getattr(choice.message, "content", base_summary) or base_summary
        except Exception:
            return base_summary
