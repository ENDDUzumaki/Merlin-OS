"""Modelos de dominio para la integración con Todoist.

Contrato estable hacia arriba: si Todoist cambia nombres de campos en su
JSON, el ajuste se hace en el client, no aquí ni en las Skills.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TodoistTask:
    id: str
    content: str
    due: str | None = None
    project_id: str | None = None
    url: str | None = None
