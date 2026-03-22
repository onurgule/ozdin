from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Return parsed JSON object from model output."""

    @abstractmethod
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 512,
    ) -> str:
        """Return plain text."""


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        """Embed a batch of texts; task_type hints retrieval_query vs retrieval_document."""


class BaseSpeechConfigProvider(ABC):
    """Hints for client-side STT/TTS; no server streaming in V1."""

    @abstractmethod
    def client_hints(self) -> dict[str, Any]:
        pass
