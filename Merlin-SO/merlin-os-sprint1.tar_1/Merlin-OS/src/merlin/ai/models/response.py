"""Response devuelta por un AIProvider.

Igual que AIRequest: contrato estable e independiente del provider concreto.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AIResponse:
    text: str
    model: str
    provider: str
    metadata: dict[str, str] = field(default_factory=dict)
