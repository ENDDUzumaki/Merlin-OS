"""Composition root del sistema.

Aquí se construyen y conectan las piezas concretas (config -> providers ->
registry -> router -> servicios). Deliberadamente NO es un Container/DI
framework: funciones explícitas son más simples y legibles que infraestructura
de inyección de dependencias genérica. Si el número de servicios crece mucho,
esto se revisita.

Este módulo es también donde se registran los handlers de intenciones. Ese
registro explícito es parte del cumplimiento de la Primera Ley: una acción
solo es ejecutable si aparece aquí, en código, no porque un LLM la nombre.
"""

from __future__ import annotations

from merlin.ai.agents.intent_classifier import IntentClassifier
from merlin.ai.memory.sqlite_store import SqliteMemoryStore
from merlin.ai.memory.store import MemoryStore
from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.router import ModelRouter
from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.ai.providers.ollama import OllamaProvider
from merlin.ai.skills.todoist_skill import TodoistSkill
from merlin.core.config import (
    load_intents_config,
    load_memory_config,
    load_models_config,
    load_personality,
    load_routing_config,
    load_secret,
    load_todoist_config,
)
from merlin.integrations.todoist.client import TodoistClient
from merlin.services.ai_service import AIService
from merlin.services.planner import IntentHandler, Planner


def build_router() -> ModelRouter:
    """Construye el ModelRouter con los providers disponibles registrados."""
    models_config = load_models_config()
    routing_config = load_routing_config()

    registry = ProviderRegistry()
    ollama_config = models_config.providers["ollama"]
    registry.register(
        OllamaProvider(
            host=ollama_config.host,
            timeout_seconds=ollama_config.timeout_seconds,
        )
    )

    return ModelRouter(registry=registry, routing_config=routing_config)


def build_ai_service() -> AIService:
    memory_config = load_memory_config()
    memory_store: MemoryStore = SqliteMemoryStore(db_path=memory_config.resolved_db_path())

    return AIService(
        router=build_router(),
        prompt_builder=PromptBuilder(personality=load_personality()),
        memory_store=memory_store,
        max_history_messages=memory_config.max_history_messages,
    )


def default_session_id() -> str:
    return load_memory_config().default_session_id


def build_todoist_skill() -> TodoistSkill:
    """Construye la Skill de Todoist. El token viene de .env, no de YAML."""
    todoist_config = load_todoist_config()
    client = TodoistClient(
        api_token=load_secret("TODOIST_API_TOKEN") or "",
        base_url=todoist_config.base_url,
        timeout_seconds=todoist_config.timeout_seconds,
    )
    return TodoistSkill(provider=client, default_list_limit=todoist_config.default_list_limit)


def build_intent_classifier() -> IntentClassifier:
    return IntentClassifier(router=build_router(), intents_config=load_intents_config())


def build_planner() -> Planner:
    """Registra qué intenciones son ejecutables y con qué Skill.

    El diccionario de handlers es la frontera de seguridad: una intención que no
    aparezca aquí no puede ejecutarse, sin importar qué produzca el modelo.
    """
    todoist = build_todoist_skill()

    async def handle_add_task(params: dict[str, str]) -> str:
        task = await todoist.add_task(params["content"], due=params.get("due"))
        due_text = f" (vence: {task.due})" if task.due else ""
        return f"Tarea creada: {task.content}{due_text}"

    async def handle_list_tasks(params: dict[str, str]) -> str:
        tasks = await todoist.list_tasks()
        if not tasks:
            return "No hay tareas activas."
        lines = [f"• {t.content}" + (f" (vence: {t.due})" if t.due else "") for t in tasks]
        return "\n".join(lines)

    handlers: dict[str, IntentHandler] = {
        "todoist.add_task": handle_add_task,
        "todoist.list_tasks": handle_list_tasks,
    }

    return Planner(intents_config=load_intents_config(), handlers=handlers)
