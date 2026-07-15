"""Inventario de providers de IA disponibles en el sistema.

El Registry solo sabe QUÉ providers existen y cómo obtenerlos por nombre.
No decide cuál usar para un request dado — eso es responsabilidad del Router.
"""

from __future__ import annotations

from merlin.ai.models.base import AIProvider


class ProviderNotFoundError(Exception):
    def __init__(self, provider_name: str) -> None:
        super().__init__(f"Provider no registrado: '{provider_name}'")


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> AIProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderNotFoundError(name) from exc

    def list_names(self) -> list[str]:
        return list(self._providers.keys())
