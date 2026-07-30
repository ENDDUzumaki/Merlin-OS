from __future__ import annotations

from merlin.ai.prompts.prompt_builder import PromptBuilder
from merlin.core.config import PersonalityConfig


def test_build_system_prompt_interpolates_personality_fields() -> None:
    personality = PersonalityConfig(
        name="Merlin",
        tone="cercano",
        language="es",
        rules=[],
        base_prompt="Eres {name}. Tono: {tone}. Idioma: {language}.",
    )
    builder = PromptBuilder(personality=personality)

    result = builder.build_system_prompt()

    assert result == "Eres Merlin. Tono: cercano. Idioma: es."


def test_build_system_prompt_appends_rules_block_when_present() -> None:
    personality = PersonalityConfig(
        name="Merlin",
        tone="cercano",
        language="es",
        rules=["Regla uno.", "Regla dos."],
        base_prompt="Eres {name}.",
    )
    builder = PromptBuilder(personality=personality)

    result = builder.build_system_prompt()

    assert "Eres Merlin." in result
    assert "Reglas:" in result
    assert "- Regla uno." in result
    assert "- Regla dos." in result


def test_build_system_prompt_omits_rules_block_when_empty() -> None:
    personality = PersonalityConfig(
        name="Merlin",
        tone="cercano",
        language="es",
        rules=[],
        base_prompt="Eres {name}.",
    )
    builder = PromptBuilder(personality=personality)

    result = builder.build_system_prompt()

    assert "Reglas:" not in result


def test_real_personality_config_enforces_spanish_only() -> None:
    """La config real debe llevar una regla explícita de idioma único.

    GLM4 tiende a filtrar caracteres chinos; la regla mitiga ese sesgo.
    """
    from merlin.core.config import load_personality

    prompt = PromptBuilder(personality=load_personality()).build_system_prompt()

    assert "español" in prompt.lower()
    assert "chino" in prompt.lower()
