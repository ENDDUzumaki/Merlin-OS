"""Clasifica una petición en lenguaje natural en una Intent.

El LLM aquí hace lo único que la Primera Ley le permite: producir texto. El
texto resultante (un JSON) se interpreta y valida en código. Un nombre de
intención emitido por el modelo no es autorización para nada — el Planner lo
verifica contra el catálogo antes de ejecutar.

Usa ModelRouter directamente y no AIService, deliberadamente: la clasificación
debe ser una extracción estructurada limpia, sin la personalidad de Merlin ni
el historial de conversación contaminando la salida, y sin ensuciar la memoria
con turnos internos del sistema.
"""

from __future__ import annotations

import json

from loguru import logger

from merlin.ai.agents.models import CONVERSATION_INTENT, Intent
from merlin.ai.models.request import AIRequest
from merlin.ai.models.router import ModelRouter
from merlin.core.config import IntentsConfig

INTENT_TASK_TYPE = "intent"

_SYSTEM_PROMPT_TEMPLATE = """\
Eres un clasificador de intenciones. Tu ÚNICA salida es un objeto JSON.

Intenciones disponibles:
{catalog}

Si la petición no corresponde a ninguna intención de la lista, responde:
{{"name": "conversation", "params": {{}}}}

Formato obligatorio de respuesta (sin markdown, sin explicaciones, solo JSON):
{{"name": "<nombre_de_intencion>", "params": {{"<param>": "<valor>"}}}}

No inventes nombres de intención que no estén en la lista.
No incluyas parámetros que no estén definidos para esa intención.\
"""


class IntentClassifier:
    def __init__(self, router: ModelRouter, intents_config: IntentsConfig) -> None:
        self._router = router
        self._intents_config = intents_config

    async def classify(self, text: str) -> Intent:
        request = AIRequest(
            prompt=text,
            system_prompt=self._build_system_prompt(),
            task_type=INTENT_TASK_TYPE,
            temperature=0.0,
        )
        response = await self._router.route(request)
        return self._parse(response.text)

    def _build_system_prompt(self) -> str:
        lines: list[str] = []
        for intent in self._intents_config.intents:
            lines.append(f"- {intent.name}: {intent.description}")
            for param in intent.params:
                flag = "obligatorio" if param.required else "opcional"
                lines.append(f"    * {param.name} ({flag}): {param.description}")
        catalog = "\n".join(lines) if lines else "(ninguna)"
        return _SYSTEM_PROMPT_TEMPLATE.format(catalog=catalog)

    def _parse(self, raw: str) -> Intent:
        """Interpreta la salida del modelo. Cualquier fallo cae a conversación."""
        payload = _extract_json_object(raw)
        if payload is None:
            logger.warning("Clasificador: salida no interpretable como JSON, uso conversación")
            return Intent(name=CONVERSATION_INTENT)

        name = payload.get("name")
        if not isinstance(name, str) or name not in self._intents_config.names:
            if name != CONVERSATION_INTENT:
                logger.warning("Clasificador: intención desconocida {!r}, uso conversación", name)
            return Intent(name=CONVERSATION_INTENT)

        return Intent(name=name, params=self._clean_params(name, payload.get("params")))

    def _clean_params(self, intent_name: str, raw_params: object) -> dict[str, str]:
        """Descarta parámetros no declarados para esa intención en el catálogo."""
        spec = self._intents_config.get(intent_name)
        if spec is None or not isinstance(raw_params, dict):
            return {}

        allowed = {param.name for param in spec.params}
        return {
            key: str(value)
            for key, value in raw_params.items()
            if key in allowed and value not in (None, "")
        }


def _extract_json_object(raw: str) -> dict | None:
    """Extrae el primer objeto JSON del texto, tolerando texto o fences alrededor."""
    start = raw.find("{")
    if start == -1:
        return None

    depth = 0
    for index in range(start, len(raw)):
        if raw[index] == "{":
            depth += 1
        elif raw[index] == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(raw[start : index + 1])
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None
