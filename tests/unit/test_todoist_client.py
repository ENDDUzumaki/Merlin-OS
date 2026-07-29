from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from merlin.integrations.todoist.client import TodoistClient, TodoistError

BASE_URL = "https://api.todoist.com/api/v1"


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> TodoistClient:
    """TodoistClient real, con un transporte simulado inyectado (sin red)."""
    return TodoistClient(
        api_token="fake-token",
        base_url=BASE_URL,
        transport=httpx.MockTransport(handler),
    )


def test_client_rejects_empty_token() -> None:
    with pytest.raises(TodoistError, match="TODOIST_API_TOKEN"):
        TodoistClient(api_token="", base_url=BASE_URL)


async def test_create_task_sends_content_and_due_string() -> None:
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["auth"] = request.headers.get("Authorization")
        captured["body"] = request.read().decode()
        return httpx.Response(
            200, json={"id": "123", "content": "Comprar leche", "due": {"string": "mañana"}}
        )

    task = await _client(handler).create_task("Comprar leche", due_string="mañana")

    assert captured["method"] == "POST"
    assert captured["url"] == f"{BASE_URL}/tasks"
    assert captured["auth"] == "Bearer fake-token"
    assert "Comprar leche" in str(captured["body"])
    assert "due_string" in str(captured["body"])
    assert task.id == "123"
    assert task.due == "mañana"


async def test_create_task_omits_due_string_when_not_given() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read().decode()
        return httpx.Response(200, json={"id": "1", "content": "Sin fecha"})

    task = await _client(handler).create_task("Sin fecha")

    assert "due_string" not in captured["body"]
    assert task.due is None


async def test_list_tasks_parses_paginated_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"id": "1", "content": "Tarea A", "due": {"date": "2026-08-01"}},
                    {"id": "2", "content": "Tarea B"},
                ],
                "next_cursor": None,
            },
        )

    tasks = await _client(handler).list_tasks(limit=10)

    assert [t.content for t in tasks] == ["Tarea A", "Tarea B"]
    assert tasks[0].due == "2026-08-01"
    assert tasks[1].due is None


async def test_list_tasks_sends_limit_as_query_param() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"results": [], "next_cursor": None})

    await _client(handler).list_tasks(limit=7)

    assert "limit=7" in captured["url"]


async def test_http_error_is_wrapped_in_todoist_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    with pytest.raises(TodoistError, match="401"):
        await _client(handler).list_tasks()
