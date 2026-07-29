"""Composition root del sistema.

Aquí se construyen y conectan las piezas concretas (config -> providers ->
registry -> router -> AIService). Deliberadamente NO es un Container/DI
framework: con un único servicio real (AIService), una función explícita
es más simple y más fácil de leer que infraestructura de inyección de
dependencias genérica. Si el número de servicios crece, esto se revisita.
"""

from __future__ import annotations

from merlin.ai.memory.sqlite_store import SqliteMemoryStore
from merlin.ai.memory.store import MemoryStore
from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.router import ModelRouter
from merlin.ai.providers.ollama import OllamaProvider
from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.core.config import (
    load_memory_config,
    load_models_config,
    load_personality,
    load_routing_config,
)
from merlin.services.ai_service import AIService


def build_ai_service() -> AIService:
    models_config = load_models_config()
    personality = load_personality()
    memory_config = load_memory_config()
    routing_config = load_routing_config()

    registry = ProviderRegistry()

    ollama_config = models_config.providers["ollama"]
    registry.register(
        OllamaProvider(
            host=ollama_config.host,
            timeout_seconds=ollama_config.timeout_seconds,
        )
    )

    router = ModelRouter(registry=registry, routing_config=routing_config)

    prompt_builder = PromptBuilder(personality=personality)
    memory_store: MemoryStore = SqliteMemoryStore(db_path=memory_config.resolved_db_path())

    return AIService(
        router=router,
        prompt_builder=prompt_builder,
        memory_store=memory_store,
        max_history_messages=memory_config.max_history_messages,
    )


def default_session_id() -> str:
    return load_memory_config().default_session_id
