"""Construye el system_prompt que acompaña a cada AIRequest.

Hoy solo interpola la personalidad configurada. Cuando exista sesión/memoria,
este es el lugar donde se combina personalidad + historial + contexto —
AIService no debe crecer para absorber esa lógica.
"""

from __future__ import annotations

from merlin.core.config import PersonalityConfig


class PromptBuilder:
    def __init__(self, personality: PersonalityConfig) -> None:
        self._personality = personality

    def build_system_prompt(self) -> str:
        prompt = self._personality.base_prompt.format(
            name=self._personality.name,
            tone=self._personality.tone,
            language=self._personality.language,
        )
        if self._personality.rules:
            rules_block = "\n".join(f"- {rule}" for rule in self._personality.rules)
            prompt = f"{prompt.strip()}\n\nReglas:\n{rules_block}"
        return prompt
