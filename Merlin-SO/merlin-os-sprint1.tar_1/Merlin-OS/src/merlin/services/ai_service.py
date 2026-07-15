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


class AIService:
    def __init__(self, router: ModelRouter) -> None:
        self._router = router

    async def ask(self, prompt: str) -> AIResponse:
        request = AIRequest(prompt=prompt)
        return await self._router.route(request)
