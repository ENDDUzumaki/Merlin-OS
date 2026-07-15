"""Selecciona el provider y modelo a usar para un AIRequest.

Hoy la política es trivial (siempre el provider/modelo por defecto de
settings.yaml). Este es el punto de extensión futuro para reglas de
selección más ricas (coste, latencia, capacidad requerida, fallback entre
providers) sin que el resto del sistema tenga que cambiar.
"""

from __future__ import annotations

from dataclasses import replace

from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse


class ModelRouter:
    def __init__(
        self,
        registry: ProviderRegistry,
        default_provider: str,
        default_model: str,
    ) -> None:
        self._registry = registry
        self._default_provider = default_provider
        self._default_model = default_model

    async def route(self, request: AIRequest) -> AIResponse:
        provider = self._registry.get(self._default_provider)
        resolved_request = (
            request if request.model is not None else self._with_default_model(request)
        )
        return await provider.generate(resolved_request)

    def _with_default_model(self, request: AIRequest) -> AIRequest:
        return replace(request, model=self._default_model)
