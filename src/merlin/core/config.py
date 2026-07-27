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


class AISettings(BaseModel):
    default_provider: str
    default_model: str


class Settings(BaseModel):
    app: AppSettings
    ai: AISettings


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


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        msg = f"Archivo de configuración no encontrado: {path}"
        raise FileNotFoundError(msg)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
