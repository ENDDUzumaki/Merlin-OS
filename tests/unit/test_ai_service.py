from __future__ import annotations

import pytest

from merlin.ai.models.base import AIProvider
from merlin.ai.models.registry import ProviderNotFoundError, ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.core.config import PersonalityConfig
from merlin.services.ai_service import AIService

TEST_PERSONALITY = PersonalityConfig(
    name="TestBot",
    tone="neutral",
    language="es",
    rules=["Nunca ejecutas acciones del sistema."],
    base_prompt="Eres {name}. Tono: {tone}. Idioma: {language}.",
)


class FakeProvider(AIProvider):
    """Provider de prueba: no hace I/O real, solo eco del prompt."""

    def __init__(self, provider_name: str = "fake") -> None:
        self._name = provider_name
        self.received_requests: list[AIRequest] = []

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, request: AIRequest) -> AIResponse:
        self.received_requests.append(request)
        return AIResponse(
            text=f"echo: {request.prompt}",
            model=request.model or "unknown",
            provider=self.name,
        )

    async def is_available(self) -> bool:
        return True


def _build_service(provider: AIProvider, default_model: str = "glm4:latest") -> AIService:
    registry = ProviderRegistry()
    registry.register(provider)
    router = ModelRouter(
        registry=registry,
        default_provider=provider.name,
        default_model=default_model,
    )
    prompt_builder = PromptBuilder(personality=TEST_PERSONALITY)
    return AIService(router=router, prompt_builder=prompt_builder)


async def test_ai_service_returns_provider_response() -> None:
    provider = FakeProvider()
    service = _build_service(provider)

    response = await service.ask("Hola")

    assert response.text == "echo: Hola"
    assert response.provider == "fake"


async def test_router_fills_default_model_when_missing() -> None:
    provider = FakeProvider()
    service = _build_service(provider, default_model="glm4:latest")

    await service.ask("Hola")

    assert provider.received_requests[0].model == "glm4:latest"


async def test_ai_service_populates_system_prompt_from_personality() -> None:
    provider = FakeProvider()
    service = _build_service(provider)

    await service.ask("Hola")

    system_prompt = provider.received_requests[0].system_prompt
    assert system_prompt is not None
    assert "TestBot" in system_prompt
    assert "Nunca ejecutas acciones del sistema." in system_prompt


async def test_registry_raises_when_provider_unknown() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ProviderNotFoundError):
        registry.get("does-not-exist")
