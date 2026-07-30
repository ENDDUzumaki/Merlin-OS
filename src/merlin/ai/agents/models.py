"""Modelos de dominio para clasificación de intenciones.

Una Intent es lo ÚNICO que el LLM produce en el flujo accionable: un nombre y
unos parámetros. No es una orden ejecutable — el Planner decide si ese nombre
corresponde a una acción registrada y permitida.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CONVERSATION_INTENT = "conversation"
"""Nombre reservado: no es una acción. Indica que la petición es solo charla.

Es el valor por defecto cuando el clasificador no reconoce nada accionable, o
cuando su respuesta no se puede interpretar (fallo seguro).
"""


@dataclass(slots=True, frozen=True)
class Intent:
    name: str
    params: dict[str, str] = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return self.name != CONVERSATION_INTENT
