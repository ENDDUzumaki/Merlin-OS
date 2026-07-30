from __future__ import annotations

from merlin.ai.agents.intent_classifier import INTENT_TASK_TYPE, IntentClassifier
from merlin.ai.agents.models import CONVERSATION_INTENT
from merlin.ai.models.base import AIProvider
from merlin.ai.models.registry import ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.core.config import IntentParamSpec, IntentsConfig, IntentSpec, RoutingConfig, RoutingRule

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
        IntentSpec(name="todoist.list_tasks", description="Listar tareas"),
    ]
)


class CannedProvider(AIProvider):
    """Devuelve una respuesta fija; registra el request recibido."""

    def __init__(self, canned_text: str) -> None:
        self._canned_text = canned_text
        self.received_requests: list[AIRequest] = []

    @property
    def name(self) -> str:
        return "canned"

    async def generate(self, request: AIRequest) -> AIResponse:
        self.received_requests.append(request)
        return AIResponse(text=self._canned_text, model="fake", provider=self.name)

    async def is_available(self) -> bool:
        return True


def _classifier(canned_text: str) -> tuple[IntentClassifier, CannedProvider]:
    provider = CannedProvider(canned_text)
    registry = ProviderRegistry()
    registry.register(provider)
    router = ModelRouter(
        registry=registry,
        routing_config=RoutingConfig(default=RoutingRule(provider="canned", model="fake")),
    )
    return IntentClassifier(router=router, intents_config=CATALOG), provider


async def test_classify_parses_clean_json() -> None:
    classifier, _ = _classifier('{"name": "todoist.add_task", "params": {"content": "leche"}}')

    intent = await classifier.classify("recuérdame comprar leche")

    assert intent.name == "todoist.add_task"
    assert intent.params == {"content": "leche"}
    assert intent.is_actionable


async def test_classify_tolerates_markdown_fences_and_surrounding_text() -> None:
    raw = 'Claro, aquí tienes:\n```json\n{"name": "todoist.list_tasks", "params": {}}\n```\nListo.'
    classifier, _ = _classifier(raw)

    intent = await classifier.classify("qué tengo pendiente")

    assert intent.name == "todoist.list_tasks"


async def test_classify_falls_back_to_conversation_on_invalid_json() -> None:
    classifier, _ = _classifier("Hola, no soy JSON en absoluto.")

    intent = await classifier.classify("hola")

    assert intent.name == CONVERSATION_INTENT
    assert not intent.is_actionable


async def test_classify_falls_back_to_conversation_on_malformed_json() -> None:
    classifier, _ = _classifier('{"name": "todoist.add_task", "params": {broken}')

    intent = await classifier.classify("algo")

    assert intent.name == CONVERSATION_INTENT


async def test_classify_rejects_intent_name_outside_catalog() -> None:
    """Primera Ley: un nombre alucinado no sobrevive al parseo."""
    classifier, _ = _classifier('{"name": "system.borrar_todo", "params": {"path": "/"}}')

    intent = await classifier.classify("borra todo")

    assert intent.name == CONVERSATION_INTENT
    assert not intent.is_actionable


async def test_classify_honors_explicit_conversation_response() -> None:
    classifier, _ = _classifier('{"name": "conversation", "params": {}}')

    intent = await classifier.classify("cuéntame un chiste")

    assert intent.name == CONVERSATION_INTENT


async def test_classify_drops_params_not_declared_in_catalog() -> None:
    raw = '{"name": "todoist.add_task", "params": {"content": "leche", "inventado": "x"}}'
    classifier, _ = _classifier(raw)

    intent = await classifier.classify("recuérdame leche")

    assert intent.params == {"content": "leche"}


async def test_classify_drops_empty_param_values() -> None:
    raw = '{"name": "todoist.add_task", "params": {"content": "leche", "due": ""}}'
    classifier, _ = _classifier(raw)

    intent = await classifier.classify("recuérdame leche")

    assert intent.params == {"content": "leche"}


async def test_classify_requests_intent_task_type_and_zero_temperature() -> None:
    classifier, provider = _classifier('{"name": "todoist.list_tasks", "params": {}}')

    await classifier.classify("qué tengo")

    request = provider.received_requests[0]
    assert request.task_type == INTENT_TASK_TYPE
    assert request.temperature == 0.0


async def test_classify_prompt_includes_catalog_names_and_params() -> None:
    classifier, provider = _classifier('{"name": "conversation", "params": {}}')

    await classifier.classify("hola")

    system_prompt = provider.received_requests[0].system_prompt or ""
    assert "todoist.add_task" in system_prompt
    assert "todoist.list_tasks" in system_prompt
    assert "content" in system_prompt


async def test_classify_does_not_send_conversation_history() -> None:
    """La clasificación debe ser limpia: sin historial ni personalidad."""
    classifier, provider = _classifier('{"name": "conversation", "params": {}}')

    await classifier.classify("hola")

    assert provider.received_requests[0].history == []
