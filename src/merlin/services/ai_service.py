"""AIService: orquesta un turno de interacción con el LLM.

Es el único punto de entrada que capas superiores (CLI hoy, Planner/Skills
en el futuro) deben conocer. No sabe de HTTP ni de Ollama — eso vive en el
Router/Registry/Provider. No decide acciones del sistema: solo produce
lenguaje, tal como exige la Primera Ley de Merlin.
"""

from __future__ import annotations

from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse
from merlin.ai.models.router import ModelRouter
from merlin.ai.prompts.prompt_builder import PromptBuilder


class AIService:
    def __init__(self, router: ModelRouter, prompt_builder: PromptBuilder) -> None:
        self._router = router
        self._prompt_builder = prompt_builder

    async def ask(self, prompt: str) -> AIResponse:
        request = AIRequest(
            prompt=prompt,
            system_prompt=self._prompt_builder.build_system_prompt(),
        )
        return await self._router.route(request)
