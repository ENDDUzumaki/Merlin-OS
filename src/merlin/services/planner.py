"""Planner: decide si una Intent puede ejecutarse, y la ejecuta.

Esta clase es donde se hace cumplir la Primera Ley de Merlin. El LLM produce
un nombre de intención; el Planner lo contrasta con un catálogo cerrado y un
diccionario explícito de handlers registrados en el composition root.

Deliberadamente NO hay dispatch dinámico: ni getattr, ni eval, ni importación
por nombre. Si el modelo alucina "system.borrar_todo", ese nombre simplemente
no existe en el diccionario y no se ejecuta nada. El LLM no puede nombrar una
acción que no haya sido registrada en código.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from loguru import logger

from merlin.ai.agents.models import Intent
from merlin.core.config import IntentsConfig

IntentHandler = Callable[[dict[str, str]], Awaitable[str]]


class UnknownIntentError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Intención no registrada: {name!r}")


class MissingHandlerError(Exception):
    """El catálogo declara una intención sin handler registrado (error de config)."""

    def __init__(self, names: set[str]) -> None:
        listed = ", ".join(sorted(names))
        super().__init__(f"Intenciones del catálogo sin handler registrado: {listed}")


class Planner:
    def __init__(
        self,
        intents_config: IntentsConfig,
        handlers: dict[str, IntentHandler],
    ) -> None:
        missing = intents_config.names - handlers.keys()
        if missing:
            raise MissingHandlerError(missing)

        self._intents_config = intents_config
        self._handlers = handlers

    async def execute(self, intent: Intent) -> str:
        handler = self._handlers.get(intent.name)
        if handler is None or intent.name not in self._intents_config.names:
            logger.warning("Planner rechazó intención no permitida: {!r}", intent.name)
            raise UnknownIntentError(intent.name)

        logger.debug("Planner ejecuta {} con {}", intent.name, intent.params)
        return await handler(intent.params)

    def requires_confirmation(self, intent: Intent) -> bool:
        """True si la intención modifica algo y debe confirmarse con el usuario.

        Las intenciones de solo lectura son idempotentes e inofensivas: pedir
        confirmación para ellas es fricción sin beneficio. El default es exigir
        confirmación: una intención desconocida o sin declarar se trata como
        escritura.
        """
        spec = self._intents_config.get(intent.name)
        if spec is None:
            return True
        return not spec.read_only

    def describe(self, intent: Intent) -> str:
        """Descripción legible de lo que se va a ejecutar, para confirmar con el usuario."""
        spec = self._intents_config.get(intent.name)
        label = spec.description if spec else intent.name
        if not intent.params:
            return label
        details = ", ".join(f"{key}={value!r}" for key, value in intent.params.items())
        return f"{label} ({details})"
