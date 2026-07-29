from __future__ import annotations

import pytest

from merlin.ai.skills.todoist_skill import TodoistSkill
from merlin.integrations.todoist.models import TodoistTask


class FakeTaskProvider:
    """Backend de tareas en memoria: sin red, registra lo que recibe."""

    def __init__(self) -> None:
        self.created: list[tuple[str, str | None]] = []
        self.list_calls: list[int] = []
        self.stored: list[TodoistTask] = []

    async def create_task(self, content: str, due_string: str | None = None) -> TodoistTask:
        self.created.append((content, due_string))
        task = TodoistTask(id=str(len(self.created)), content=content, due=due_string)
        self.stored.append(task)
        return task

    async def list_tasks(self, limit: int = 20) -> list[TodoistTask]:
        self.list_calls.append(limit)
        return self.stored[:limit]


async def test_add_task_forwards_content_and_due() -> None:
    provider = FakeTaskProvider()
    skill = TodoistSkill(provider=provider)

    task = await skill.add_task("Comprar leche", due="mañana")

    assert provider.created == [("Comprar leche", "mañana")]
    assert task.content == "Comprar leche"
    assert task.due == "mañana"


async def test_add_task_strips_whitespace() -> None:
    provider = FakeTaskProvider()
    skill = TodoistSkill(provider=provider)

    await skill.add_task("  Comprar pan  ")

    assert provider.created == [("Comprar pan", None)]


async def test_add_task_rejects_empty_content() -> None:
    skill = TodoistSkill(provider=FakeTaskProvider())

    with pytest.raises(ValueError, match="no puede estar vacío"):
        await skill.add_task("   ")


async def test_list_tasks_uses_default_limit_when_not_given() -> None:
    provider = FakeTaskProvider()
    skill = TodoistSkill(provider=provider, default_list_limit=5)

    await skill.list_tasks()

    assert provider.list_calls == [5]


async def test_list_tasks_respects_explicit_limit() -> None:
    provider = FakeTaskProvider()
    skill = TodoistSkill(provider=provider, default_list_limit=5)

    await skill.list_tasks(limit=2)

    assert provider.list_calls == [2]


async def test_list_tasks_returns_created_tasks() -> None:
    provider = FakeTaskProvider()
    skill = TodoistSkill(provider=provider)

    await skill.add_task("Tarea 1")
    await skill.add_task("Tarea 2")
    tasks = await skill.list_tasks()

    assert [t.content for t in tasks] == ["Tarea 1", "Tarea 2"]
