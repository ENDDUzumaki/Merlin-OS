"""Skill de gestión de tareas vía Todoist.

Las Skills son las únicas piezas del sistema autorizadas a ejecutar acciones
reales. El LLM nunca las invoca por su cuenta: hoy las invoca la CLI, y en el
futuro las invocará el Planner. Esto es la Primera Ley de Merlin en la
práctica — de hecho, esta Skill funciona sin que ningún modelo participe.

Depende de un Protocol (TaskProvider), no de TodoistClient concreto, para
poder testearse sin red y para admitir otro backend de tareas más adelante.
"""

from __future__ import annotations

from typing import Protocol

from merlin.integrations.todoist.models import TodoistTask


class TaskProvider(Protocol):
    """Contrato mínimo que la Skill necesita de un backend de tareas."""

    async def create_task(self, content: str, due_string: str | None = None) -> TodoistTask: ...

    async def list_tasks(self, limit: int = 20) -> list[TodoistTask]: ...


class TodoistSkill:
    name = "todoist"

    def __init__(self, provider: TaskProvider, default_list_limit: int = 20) -> None:
        self._provider = provider
        self._default_list_limit = default_list_limit

    async def add_task(self, content: str, due: str | None = None) -> TodoistTask:
        """Crea una tarea. `due` acepta lenguaje natural ('mañana', 'lunes 9am')."""
        if not content.strip():
            msg = "El contenido de la tarea no puede estar vacío"
            raise ValueError(msg)
        return await self._provider.create_task(content=content.strip(), due_string=due)

    async def list_tasks(self, limit: int | None = None) -> list[TodoistTask]:
        """Devuelve las tareas activas, hasta `limit`."""
        return await self._provider.list_tasks(limit=limit or self._default_list_limit)
