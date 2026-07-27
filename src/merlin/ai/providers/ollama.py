"""Provider concreto que habla con un servidor Ollama local.

Único módulo del sistema que conoce el protocolo HTTP de Ollama. Si Ollama
cambia su API, el cambio se contiene aquí.
"""

from __future__ import annotations

import httpx
from loguru import logger

from merlin.ai.models.base import AIProvider
from merlin.ai.models.request import AIRequest
from merlin.ai.models.response import AIResponse


class OllamaProvider(AIProvider):
    def __init__(self, host: str, timeout_seconds: int = 120) -> None:
        self._host = host.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, request: AIRequest) -> AIResponse:
        if request.model is None:
            msg = "OllamaProvider requiere AIRequest.model (ningún default implícito)"
            raise ValueError(msg)

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for turn in request.history:
            messages.append({"role": turn.role.value, "content": turn.content})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, object] = {
            "model": request.model,
            "messages": messages,
            "stream": False,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}

        logger.debug("Ollama request -> model={} host={}", request.model, self._host)

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            resp = await client.post(f"{self._host}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return AIResponse(
            text=data.get("message", {}).get("content", ""),
            model=request.model,
            provider=self.name,
        )

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._host}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
