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
