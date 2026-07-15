"""Contrato que todo AIProvider debe cumplir.

Un AIProvider solo sabe generar texto a partir de un AIRequest. No conoce
Skills, Intents ni el Kernel — eso viola la Primera Ley de Merlin
("The LLM never controls the system").
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse


class AIProvider(ABC):
    """Interfaz base para cualquier proveedor de modelos de IA."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador único del provider (p. ej. 'ollama')."""

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Genera una respuesta a partir de un AIRequest."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Indica si el provider está operativo (servicio arriba, etc.)."""
