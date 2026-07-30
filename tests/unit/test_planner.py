from __future__ import annotations

import pytest

from merlin.ai.agents.models import Intent
from merlin.core.config import IntentsConfig, IntentParamSpec, IntentSpec
from merlin.services.planner import (
    IntentHandler,
    MissingHandlerError,
    Planner,
    UnknownIntentError,
)

CATALOG = IntentsConfig(
    intents=[
        IntentSpec(
            name="todoist.add_task",
            description="Crear una tarea",
            params=[
                IntentParamSpec(name="content", description="Qué hacer", required=True),
                IntentParamSpec(name="due", description="Cuándo", required=False),
            ],
        ),
        IntentSpec(name="todoist.list_tasks", description="Listar tareas", read_only=True),
    ]
)


def _handlers(calls: list[tuple[str, dict[str, str]]]) -> dict[str, IntentHandler]:
    async def add_task(params: dict[str, str]) -> str:
        calls.append(("todoist.add_task", params))
        return "tarea creada"

    async def list_tasks(params: dict[str, str]) -> str:
        calls.append(("todoist.list_tasks", params))
        return "sin tareas"

    return {"todoist.add_task": add_task, "todoist.list_tasks": list_tasks}


async def test_execute_calls_registered_handler_with_params() -> None:
    calls: list[tuple[str, dict[str, str]]] = []
    planner = Planner(intents_config=CATALOG, handlers=_handlers(calls))

    result = await planner.execute(
        Intent(name="todoist.add_task", params={"content": "leche", "due": "mañana"})
    )

    assert result == "tarea creada"
    assert calls == [("todoist.add_task", {"content": "leche", "due": "mañana"})]


async def test_execute_rejects_hallucinated_intent_name() -> None:
    """Primera Ley: un nombre inventado por el LLM no ejecuta nada."""
    calls: list[tuple[str, dict[str, str]]] = []
    planner = Planner(intents_config=CATALOG, handlers=_handlers(calls))

    with pytest.raises(UnknownIntentError):
        await planner.execute(Intent(name="system.borrar_todo", params={"path": "/"}))

    assert calls == []


async def test_execute_rejects_intent_absent_from_catalog_even_if_handler_exists() -> None:
    """La allowlist del catálogo manda, no solo la existencia del handler."""
    calls: list[tuple[str, dict[str, str]]] = []
    handlers = _handlers(calls)

    async def secret_handler(params: dict[str, str]) -> str:
        calls.append(("oculto", params))
        return "ejecutado"

    handlers["accion.oculta"] = secret_handler
    planner = Planner(intents_config=CATALOG, handlers=handlers)

    with pytest.raises(UnknownIntentError):
        await planner.execute(Intent(name="accion.oculta"))

    assert calls == []


def test_planner_fails_fast_when_catalog_intent_has_no_handler() -> None:
    """Error de configuración detectado al arrancar, no en tiempo de ejecución."""
    with pytest.raises(MissingHandlerError, match="todoist.list_tasks"):
        Planner(intents_config=CATALOG, handlers={"todoist.add_task": _handlers([])["todoist.add_task"]})


def test_describe_includes_description_and_params() -> None:
    planner = Planner(intents_config=CATALOG, handlers=_handlers([]))

    text = planner.describe(Intent(name="todoist.add_task", params={"content": "leche"}))

    assert "Crear una tarea" in text
    assert "leche" in text


def test_describe_without_params_returns_only_description() -> None:
    planner = Planner(intents_config=CATALOG, handlers=_handlers([]))

    assert planner.describe(Intent(name="todoist.list_tasks")) == "Listar tareas"


def test_write_intent_requires_confirmation() -> None:
    planner = Planner(intents_config=CATALOG, handlers=_handlers([]))

    assert planner.requires_confirmation(Intent(name="todoist.add_task")) is True


def test_read_only_intent_does_not_require_confirmation() -> None:
    planner = Planner(intents_config=CATALOG, handlers=_handlers([]))

    assert planner.requires_confirmation(Intent(name="todoist.list_tasks")) is False


def test_unknown_intent_requires_confirmation_by_default() -> None:
    """Ante lo desconocido, el default seguro es exigir confirmación."""
    planner = Planner(intents_config=CATALOG, handlers=_handlers([]))

    assert planner.requires_confirmation(Intent(name="algo.desconocido")) is True
