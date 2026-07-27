"""Request enviado hacia un AIProvider.

Es un contrato estable: ningún provider concreto debe filtrar sus propios
detalles (payloads HTTP, nombres de campos internos, etc.) hacia arriba.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True, frozen=True)
class ConversationTurn:
    role: MessageRole
    content: str


@dataclass(slots=True, frozen=True)
class AIRequest:
    prompt: str
    model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None
    history: list[ConversationTurn] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
