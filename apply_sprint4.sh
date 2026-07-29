#!/usr/bin/env bash
set -euo pipefail
echo "Aplicando Sprint 4: Model Router más rico..."

mkdir -p config
cat > config/settings.yaml << 'MERLIN_EOF'
app:
  name: "Merlin OS"
  log_level: "INFO"
MERLIN_EOF
echo "  escrito: config/settings.yaml"

mkdir -p config
cat > config/routing.yaml << 'MERLIN_EOF'
default:
  provider: ollama
  model: glm4:latest

tasks:
  code:
    provider: ollama
    model: qwen2.5-coder:latest
  lightweight:
    provider: ollama
    model: qwen3:4b
  creative:
    provider: ollama
    model: gemma4:latest
MERLIN_EOF
echo "  escrito: config/routing.yaml"

mkdir -p src/merlin/ai/models
cat > src/merlin/ai/models/request.py << 'MERLIN_EOF'
"""Request enviado hacia un AIProvider.

Es un contrato estable: ningún provider concreto debe filtrar sus propios
detalles (payloads HTTP, nombres de campos internos, etc.) hacia arriba.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True, frozen=True)
class ConversationTurn:
    role: MessageRole
    content: str


@dataclass(slots=True, frozen=True)
class AIRequest:
    prompt: str
    model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None
    history: list[ConversationTurn] = field(default_factory=list)
    task_type: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
MERLIN_EOF
echo "  escrito: src/merlin/ai/models/request.py"

mkdir -p src/merlin/ai/models
cat > src/merlin/ai/models/router.py << 'MERLIN_EOF'
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
MERLIN_EOF
echo "  escrito: src/merlin/ai/models/router.py"

mkdir -p src/merlin/core
cat > src/merlin/core/bootstrap.py << 'MERLIN_EOF'
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
MERLIN_EOF
echo "  escrito: src/merlin/core/bootstrap.py"

mkdir -p src/merlin/core
cat > src/merlin/core/config.py << 'MERLIN_EOF'
"""Carga de configuración del sistema desde YAML.

Toda configuración operativa (modelo por defecto, host, timeout, temperatura)
vive aquí. Ningún otro módulo debe hardcodear estos valores.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
PROJECT_ROOT = DEFAULT_CONFIG_DIR.parent


class AppSettings(BaseModel):
    name: str
    log_level: str = "INFO"


class Settings(BaseModel):
    app: AppSettings


class ModelSpec(BaseModel):
    name: str
    temperature: float = 0.7


class ProviderConfig(BaseModel):
    host: str
    timeout_seconds: int = 120
    models: list[ModelSpec] = Field(default_factory=list)


class ModelsConfig(BaseModel):
    providers: dict[str, ProviderConfig]


class PersonalityConfig(BaseModel):
    name: str
    tone: str
    language: str
    rules: list[str] = Field(default_factory=list)
    base_prompt: str


class MemoryConfig(BaseModel):
    db_path: Path
    max_history_messages: int = 20
    default_session_id: str = "default"

    def resolved_db_path(self) -> Path:
        if self.db_path.is_absolute():
            return self.db_path
        return PROJECT_ROOT / self.db_path


class RoutingRule(BaseModel):
    provider: str
    model: str


class RoutingConfig(BaseModel):
    default: RoutingRule
    tasks: dict[str, RoutingRule] = Field(default_factory=dict)


def load_settings(config_dir: Path = DEFAULT_CONFIG_DIR) -> Settings:
    """Carga config/settings.yaml."""
    data = _read_yaml(config_dir / "settings.yaml")
    return Settings.model_validate(data)


def load_models_config(config_dir: Path = DEFAULT_CONFIG_DIR) -> ModelsConfig:
    """Carga config/models.yaml."""
    data = _read_yaml(config_dir / "models.yaml")
    return ModelsConfig.model_validate(data)


def load_personality(config_dir: Path = DEFAULT_CONFIG_DIR) -> PersonalityConfig:
    """Carga config/personality.yaml."""
    data = _read_yaml(config_dir / "personality.yaml")
    return PersonalityConfig.model_validate(data)


def load_memory_config(config_dir: Path = DEFAULT_CONFIG_DIR) -> MemoryConfig:
    """Carga config/memory.yaml."""
    data = _read_yaml(config_dir / "memory.yaml")
    return MemoryConfig.model_validate(data)


def load_routing_config(config_dir: Path = DEFAULT_CONFIG_DIR) -> RoutingConfig:
    """Carga config/routing.yaml."""
    data = _read_yaml(config_dir / "routing.yaml")
    return RoutingConfig.model_validate(data)


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        msg = f"Archivo de configuración no encontrado: {path}"
        raise FileNotFoundError(msg)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
MERLIN_EOF
echo "  escrito: src/merlin/core/config.py"

mkdir -p src/merlin/runtime
cat > src/merlin/runtime/cli.py << 'MERLIN_EOF'
"""Interfaz de línea de comandos de Merlin OS.

Capa de presentación: traduce input del usuario a llamadas al AIService y
formatea la salida. No contiene lógica de negocio ni conoce providers.
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from merlin.core.bootstrap import build_ai_service, default_session_id

app = typer.Typer(name="merlin", help="Merlin OS — Personal Cognitive Operating System")
console = Console()


@app.callback()
def main() -> None:
    """Merlin OS CLI. Ejemplo: merlin ask "Hola"."""


@app.command()
def ask(
    prompt: str,
    session: str = typer.Option(None, help="ID de sesión de memoria. Por defecto: la de config."),
    task: str = typer.Option(
        None, "--task", help="Tipo de tarea para elegir modelo (ver config/routing.yaml)."
    ),
) -> None:
    """Envía un prompt al modelo por defecto y muestra la respuesta."""
    ai_service = build_ai_service()
    session_id = session or default_session_id()

    with console.status("[bold cyan]Pensando..."):
        response = asyncio.run(ai_service.ask(prompt, session_id=session_id, task_type=task))

    console.print(f"[bold green]{response.provider}/{response.model}:[/bold green]")
    console.print(response.text)


if __name__ == "__main__":
    app()
MERLIN_EOF
echo "  escrito: src/merlin/runtime/cli.py"

mkdir -p src/merlin/services
cat > src/merlin/services/ai_service.py << 'MERLIN_EOF'
"""AIService: orquesta un turno de interacción con el LLM.

Es el único punto de entrada que capas superiores (CLI hoy, Planner/Skills
en el futuro) deben conocer. No sabe de HTTP ni de Ollama — eso vive en el
Router/Registry/Provider. No decide acciones del sistema: solo produce
lenguaje, tal como exige la Primera Ley de Merlin.

También es responsable de leer y persistir el historial de conversación vía
MemoryStore, para que ni el Router ni los Providers necesiten saber que la
memoria existe.
"""

from __future__ import annotations

from merlin.ai.memory.store import MemoryStore
from merlin.ai.models.request import AIRequest, ConversationTurn, MessageRole
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.ai.prompts.prompt_builder import PromptBuilder


class AIService:
    def __init__(
        self,
        router: ModelRouter,
        prompt_builder: PromptBuilder,
        memory_store: MemoryStore,
        max_history_messages: int,
    ) -> None:
        self._router = router
        self._prompt_builder = prompt_builder
        self._memory_store = memory_store
        self._max_history_messages = max_history_messages

    async def ask(
        self,
        prompt: str,
        session_id: str,
        task_type: str | None = None,
    ) -> AIResponse:
        recent = await self._memory_store.get_recent(session_id, self._max_history_messages)
        history = [ConversationTurn(role=m.role, content=m.content) for m in recent]

        request = AIRequest(
            prompt=prompt,
            system_prompt=self._prompt_builder.build_system_prompt(),
            history=history,
            task_type=task_type,
        )
        response = await self._router.route(request)

        await self._memory_store.append(session_id, MessageRole.USER, prompt)
        await self._memory_store.append(session_id, MessageRole.ASSISTANT, response.text)

        return response
MERLIN_EOF
echo "  escrito: src/merlin/services/ai_service.py"

mkdir -p tests/unit
cat > tests/unit/test_ai_service.py << 'MERLIN_EOF'
from __future__ import annotations

import pytest

from merlin.ai.models.base import AIProvider
from merlin.ai.models.registry import ProviderNotFoundError, ProviderRegistry
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.core.config import PersonalityConfig, RoutingConfig, RoutingRule
from merlin.services.ai_service import AIService
from tests.unit.fakes import FakeMemoryStore

TEST_PERSONALITY = PersonalityConfig(
    name="TestBot",
    tone="neutral",
    language="es",
    rules=["Nunca ejecutas acciones del sistema."],
    base_prompt="Eres {name}. Tono: {tone}. Idioma: {language}.",
)

TEST_SESSION = "test-session"


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


def _build_service(
    provider: AIProvider,
    default_model: str = "glm4:latest",
    memory_store: FakeMemoryStore | None = None,
    max_history_messages: int = 20,
    tasks: dict[str, RoutingRule] | None = None,
) -> AIService:
    registry = ProviderRegistry()
    registry.register(provider)
    routing_config = RoutingConfig(
        default=RoutingRule(provider=provider.name, model=default_model),
        tasks=tasks or {},
    )
    router = ModelRouter(registry=registry, routing_config=routing_config)
    prompt_builder = PromptBuilder(personality=TEST_PERSONALITY)
    return AIService(
        router=router,
        prompt_builder=prompt_builder,
        memory_store=memory_store or FakeMemoryStore(),
        max_history_messages=max_history_messages,
    )


async def test_ai_service_returns_provider_response() -> None:
    provider = FakeProvider()
    service = _build_service(provider)

    response = await service.ask("Hola", session_id=TEST_SESSION)

    assert response.text == "echo: Hola"
    assert response.provider == "fake"


async def test_router_fills_default_model_when_missing() -> None:
    provider = FakeProvider()
    service = _build_service(provider, default_model="glm4:latest")

    await service.ask("Hola", session_id=TEST_SESSION)

    assert provider.received_requests[0].model == "glm4:latest"


async def test_ai_service_populates_system_prompt_from_personality() -> None:
    provider = FakeProvider()
    service = _build_service(provider)

    await service.ask("Hola", session_id=TEST_SESSION)

    system_prompt = provider.received_requests[0].system_prompt
    assert system_prompt is not None
    assert "TestBot" in system_prompt
    assert "Nunca ejecutas acciones del sistema." in system_prompt


async def test_router_uses_task_specific_model_when_task_type_matches() -> None:
    provider = FakeProvider()
    service = _build_service(
        provider,
        default_model="glm4:latest",
        tasks={"code": RoutingRule(provider=provider.name, model="qwen2.5-coder:latest")},
    )

    response = await service.ask("Escribe una función", session_id=TEST_SESSION, task_type="code")

    assert response.model == "qwen2.5-coder:latest"


async def test_router_falls_back_to_default_when_task_type_unknown() -> None:
    provider = FakeProvider()
    service = _build_service(
        provider,
        default_model="glm4:latest",
        tasks={"code": RoutingRule(provider=provider.name, model="qwen2.5-coder:latest")},
    )

    response = await service.ask("Hola", session_id=TEST_SESSION, task_type="tarea-inexistente")

    assert response.model == "glm4:latest"


async def test_router_falls_back_to_default_when_task_type_is_none() -> None:
    provider = FakeProvider()
    service = _build_service(
        provider,
        default_model="glm4:latest",
        tasks={"code": RoutingRule(provider=provider.name, model="qwen2.5-coder:latest")},
    )

    response = await service.ask("Hola", session_id=TEST_SESSION)

    assert response.model == "glm4:latest"


async def test_ai_service_persists_user_and_assistant_turns() -> None:
    provider = FakeProvider()
    memory_store = FakeMemoryStore()
    service = _build_service(provider, memory_store=memory_store)

    await service.ask("Hola", session_id=TEST_SESSION)

    stored = await memory_store.get_recent(TEST_SESSION, limit=10)
    assert [m.content for m in stored] == ["Hola", "echo: Hola"]


async def test_ai_service_sends_previous_history_to_provider() -> None:
    provider = FakeProvider()
    memory_store = FakeMemoryStore()
    service = _build_service(provider, memory_store=memory_store)

    await service.ask("Primer mensaje", session_id=TEST_SESSION)
    await service.ask("Segundo mensaje", session_id=TEST_SESSION)

    second_request = provider.received_requests[1]
    assert len(second_request.history) == 2
    assert second_request.history[0].content == "Primer mensaje"
    assert second_request.history[1].content == "echo: Primer mensaje"


async def test_ai_service_keeps_sessions_isolated() -> None:
    provider = FakeProvider()
    memory_store = FakeMemoryStore()
    service = _build_service(provider, memory_store=memory_store)

    await service.ask("Hola desde sesión A", session_id="session-a")
    await service.ask("Hola desde sesión B", session_id="session-b")

    history_b = await memory_store.get_recent("session-b", limit=10)
    assert len(history_b) == 2
    assert history_b[0].content == "Hola desde sesión B"


async def test_registry_raises_when_provider_unknown() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ProviderNotFoundError):
        registry.get("does-not-exist")
MERLIN_EOF
echo "  escrito: tests/unit/test_ai_service.py"

mkdir -p tests/unit
cat > tests/unit/test_model_router.py << 'MERLIN_EOF'
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
MERLIN_EOF
echo "  escrito: tests/unit/test_model_router.py"

echo ""
echo "Listo. Corre: uv run pytest -v"
