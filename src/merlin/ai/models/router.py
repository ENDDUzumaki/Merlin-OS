"""Selecciona el provider y modelo a usar para un AIRequest.

La política de selección vive en config/routing.yaml (RoutingConfig), no en
código: agregar un nuevo tipo de tarea es editar YAML, no tocar esta clase.
Este sigue siendo el único punto de extensión futuro para reglas más ricas
(coste, latencia, fallback entre providers).
"""

from __future__ import annotations

from dataclasses import replace

from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.core.config import RoutingConfig


class ModelRouter:
    def __init__(
        self,
        registry: ProviderRegistry,
        routing_config: RoutingConfig,
    ) -> None:
        self._registry = registry
        self._routing_config = routing_config

    async def route(self, request: AIRequest) -> AIResponse:
        if request.model is not None:
            provider = self._registry.get(self._routing_config.default.provider)
            return await provider.generate(request)

        rule = self._routing_config.default
        if request.task_type is not None and request.task_type in self._routing_config.tasks:
            rule = self._routing_config.tasks[request.task_type]

        provider = self._registry.get(rule.provider)
        resolved_request = replace(request, model=rule.model)
        return await provider.generate(resolved_request)
