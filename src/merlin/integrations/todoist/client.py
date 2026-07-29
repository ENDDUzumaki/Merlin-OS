"""Cliente HTTP para la API v1 de Todoist.

Único módulo del sistema que conoce el protocolo de Todoist (endpoints,
forma del JSON, cabeceras de auth). Si Todoist cambia su API, el cambio se
contiene aquí.

Nota: la REST API v2 fue descontinuada en febrero de 2026. Este cliente usa
la API unificada v1 (https://api.todoist.com/api/v1), cuyos endpoints de
listado son paginados y devuelven {"results": [...], "next_cursor": ...}.
"""

from __future__ import annotations

import httpx
from loguru import logger

from merlin.integrations.todoist.models import TodoistTask


class TodoistError(Exception):
    """Fallo al comunicarse con Todoist o respuesta inesperada."""


class TodoistClient:
    def __init__(
        self,
        api_token: str,
        base_url: str,
        timeout_seconds: int = 30,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_token:
            msg = "TODOIST_API_TOKEN no está configurado (revisa tu archivo .env)"
            raise TodoistError(msg)
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

    async def create_task(self, content: str, due_string: str | None = None) -> TodoistTask:
        payload: dict[str, str] = {"content": content}
        if due_string:
            payload["due_string"] = due_string

        logger.debug("Todoist create_task -> content={!r} due={!r}", content, due_string)
        data = await self._request("POST", "/tasks", json=payload)
        if not isinstance(data, dict):
            msg = f"Respuesta inesperada al crear tarea: {type(data).__name__}"
            raise TodoistError(msg)
        return self._to_task(data)

    async def list_tasks(self, limit: int = 20) -> list[TodoistTask]:
        logger.debug("Todoist list_tasks -> limit={}", limit)
        data = await self._request("GET", "/tasks", params={"limit": limit})
        results = data.get("results") if isinstance(data, dict) else data
        if not isinstance(results, list):
            msg = "Respuesta inesperada al listar tareas: no se encontró una lista"
            raise TodoistError(msg)
        return [self._to_task(item) for item in results if isinstance(item, dict)]

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, str] | None = None,
        params: dict[str, int] | None = None,
    ) -> dict | list:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds, transport=self._transport
            ) as client:
                resp = await client.request(
                    method, url, headers=self._headers, json=json, params=params
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            msg = f"Todoist respondió {exc.response.status_code} en {method} {path}"
            raise TodoistError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Fallo de red al llamar a Todoist ({method} {path})"
            raise TodoistError(msg) from exc

    @staticmethod
    def _to_task(data: dict) -> TodoistTask:
        due = data.get("due")
        due_text: str | None = None
        if isinstance(due, dict):
            due_text = due.get("string") or due.get("date")

        return TodoistTask(
            id=str(data.get("id", "")),
            content=str(data.get("content", "")),
            due=due_text,
            project_id=str(data["project_id"]) if data.get("project_id") else None,
            url=data.get("url"),
        )
