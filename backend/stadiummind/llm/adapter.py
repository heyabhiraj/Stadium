"""Large-Language-Model adapters (the "explain" half of the product).

The AI layer never talks to a vendor SDK directly; it depends on the abstract
:class:`LLMAdapter`. This is the Strategy pattern and it buys us three things:

1. **Testability** - :class:`MockLLM` is deterministic, offline and free, so
   the whole agent pipeline can be unit- and system-tested with no network.
2. **Swappability** - :class:`GeminiLLM` wraps Google's Generative AI SDK and
   is selected automatically when ``GEMINI_API_KEY`` is present.
3. **Resilience** - if a real Gemini call fails at runtime, the orchestrator
   can fall back to the mock so a live demo never hard-crashes.

Set ``GEMINI_API_KEY`` (and optionally ``GEMINI_MODEL``) to use real Gemini.
"""

from __future__ import annotations

import logging
import textwrap
from abc import ABC, abstractmethod

from stadiummind.core.config import Settings, get_settings
from stadiummind.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """Abstract text-in/text-out language model."""

    #: Short identifier for logging / API responses.
    name: str = "abstract"

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Return the model's completion for ``prompt``."""

    def explain(self, context: str, question: str) -> str:
        """Convenience helper used by agents to turn context into prose."""
        system = (
            "You are StadiumMind, a concise assistant for a FIFA World Cup "
            "stadium. Explain the situation in 1-2 short sentences, then give a "
            "clear recommendation. Never invent data."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        return self.complete(prompt, system=system)


class MockLLM(LLMAdapter):
    """Deterministic, offline stand-in for a real model.

    It does *not* attempt to be clever: it echoes the salient context back as a
    clean explanation. That determinism is exactly what makes tests reliable.
    """

    name = "mock"

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        # Extract the question if present for a slightly more natural reply.
        question = ""
        if "Question:" in prompt:
            question = prompt.split("Question:", 1)[1].strip()
        context = prompt
        if "Context:" in prompt:
            context = prompt.split("Context:", 1)[1]
            if "Question:" in context:
                context = context.split("Question:", 1)[0]
        context = " ".join(context.split())
        reply = context[:240] if context else "No additional context available."
        suffix = f" (re: {question})" if question else ""
        return textwrap.shorten(f"{reply}{suffix}", width=320, placeholder=" ...")


class GeminiLLM(LLMAdapter):  # pragma: no cover - requires network + API key
    """Adapter over Google's Gemini via the ``google-generativeai`` SDK."""

    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        import google.generativeai as genai  # optional dependency

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._timeout = timeout

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            response = self._model.generate_content(
                full_prompt,
                request_options={"timeout": self._timeout},
            )
            return (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Gemini call failed: {exc}") from exc


def build_llm(settings: Settings | None = None) -> LLMAdapter:
    """Factory: real Gemini when configured, otherwise the deterministic mock."""
    settings = settings or get_settings()
    if settings.gemini_enabled:
        try:
            return GeminiLLM(
                api_key=settings.gemini_api_key,  # type: ignore[arg-type]
                model=settings.gemini_model,
                timeout=settings.llm_timeout_seconds,
            )
        except Exception:  # noqa: BLE001 - SDK missing or misconfigured
            logger.warning("Gemini unavailable; using MockLLM")
    return MockLLM()
