"""Request enviado hacia un AIProvider.

Es un contrato estable: ningún provider concreto debe filtrar sus propios
detalles (payloads HTTP, nombres de campos internos, etc.) hacia arriba.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AIRequest:
    prompt: str
    model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
