"""Modelos de dominio para la memoria de conversación."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from merlin.ai.models.request import MessageRole

__all__ = ["MemoryMessage", "MessageRole"]


@dataclass(slots=True, frozen=True)
class MemoryMessage:
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime
