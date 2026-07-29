from __future__ import annotations

from merlin.ai.models.base import AIProvider
from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.core.config import RoutingConfig, RoutingRule


class RecordingProvider(AIProvider):
    def __init__(self, provider_name: str) -> None:
        self._name = provider_name
        self.received_requests: list[AIRequest] = []

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, request: AIRequest) -> AIResponse:
        self.received_requests.append(request)
        return AIResponse(text="ok", model=request.model or "unknown", provider=self.name)

    async def is_available(self) -> bool:
        return True


def _registry_with(*providers: AIProvider) -> ProviderRegistry:
    registry = ProviderRegistry()
    for provider in providers:
        registry.register(provider)
    return registry


async def test_route_uses_default_rule_when_no_task_type() -> None:
    provider = RecordingProvider("ollama")
    routing_config = RoutingConfig(default=RoutingRule(provider="ollama", model="glm4:latest"))
    router = ModelRouter(registry=_registry_with(provider), routing_config=routing_config)

    await router.route(AIRequest(prompt="Hola"))

    assert provider.received_requests[0].model == "glm4:latest"


async def test_route_uses_task_rule_when_task_type_matches() -> None:
    provider = RecordingProvider("ollama")
    routing_config = RoutingConfig(
        default=RoutingRule(provider="ollama", model="glm4:latest"),
        tasks={"code": RoutingRule(provider="ollama", model="qwen2.5-coder:latest")},
    )
    router = ModelRouter(registry=_registry_with(provider), routing_config=routing_config)

    await router.route(AIRequest(prompt="Escribe código", task_type="code"))

    assert provider.received_requests[0].model == "qwen2.5-coder:latest"


async def test_route_can_select_different_provider_per_task() -> None:
    ollama = RecordingProvider("ollama")
    other = RecordingProvider("other")
    routing_config = RoutingConfig(
        default=RoutingRule(provider="ollama", model="glm4:latest"),
        tasks={"special": RoutingRule(provider="other", model="special-model")},
    )
    router = ModelRouter(registry=_registry_with(ollama, other), routing_config=routing_config)

    response = await router.route(AIRequest(prompt="Hola", task_type="special"))

    assert response.provider == "other"
    assert ollama.received_requests == []
    assert other.received_requests[0].model == "special-model"


async def test_route_respects_explicit_model_when_already_set() -> None:
    provider = RecordingProvider("ollama")
    routing_config = RoutingConfig(
        default=RoutingRule(provider="ollama", model="glm4:latest"),
        tasks={"code": RoutingRule(provider="ollama", model="qwen2.5-coder:latest")},
    )
    router = ModelRouter(registry=_registry_with(provider), routing_config=routing_config)

    await router.route(AIRequest(prompt="Hola", model="modelo-explicito", task_type="code"))

    assert provider.received_requests[0].model == "modelo-explicito"
