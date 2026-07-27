"""Contrato que todo almacén de memoria debe cumplir.

AIService depende de esta interfaz, no de una base de datos concreta.
Permite cambiar el backend (SQLite hoy, otro mañana) sin tocar el servicio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from merlin.ai.memory.models import MemoryMessage, MessageRole


class MemoryStore(ABC):
    @abstractmethod
    async def append(self, session_id: str, role: MessageRole, content: str) -> None:
        """Persiste un nuevo mensaje en el historial de la sesión."""

    @abstractmethod
    async def get_recent(self, session_id: str, limit: int) -> list[MemoryMessage]:
        """Devuelve los últimos `limit` mensajes de la sesión, en orden cronológico."""
