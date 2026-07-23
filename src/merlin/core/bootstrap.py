"""Composition root del sistema.

Aquí se construyen y conectan las piezas concretas (config -> providers ->
registry -> router -> AIService). Deliberadamente NO es un Container/DI
framework: con un único servicio real (AIService), una función explícita
es más simple y más fácil de leer que infraestructura de inyección de
dependencias genérica. Si el número de servicios crece, esto se revisita.
"""

from __future__ import annotations

from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.router import ModelRouter
from merlin.ai.providers.ollama import OllamaProvider
from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.core.config import load_models_config, load_personality, load_settings
from merlin.services.ai_service import AIService


def build_ai_service() -> AIService:
    settings = load_settings()
    models_config = load_models_config()
    personality = load_personality()

    registry = ProviderRegistry()

    ollama_config = models_config.providers["ollama"]
    registry.register(
        OllamaProvider(
            host=ollama_config.host,
            timeout_seconds=ollama_config.timeout_seconds,
        )
    )

    router = ModelRouter(
        registry=registry,
        default_provider=settings.ai.default_provider,
        default_model=settings.ai.default_model,
    )

    prompt_builder = PromptBuilder(personality=personality)

    return AIService(router=router, prompt_builder=prompt_builder)
