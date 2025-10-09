"""
Centralized configuration loading for RMTool.

Loads settings from environment variables (with optional .env support),
validates required values, and exposes helper utilities to instantiate
LLM providers declared in `rmtool.agent.llm_provider`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar, Dict, Optional, Set

from dotenv import load_dotenv
try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
except ImportError:  # pragma: no cover - compatibility for Pydantic v1
    from pydantic import BaseModel, Field, ValidationError, validator as field_validator  # type: ignore

from rmtool.agent.llm_provider import (
    LLMError,
    LLMProvider,
    get_provider,
)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read environment variable with optional default."""
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _parse_bool(value: Optional[str], default: bool) -> bool:
    """Parse boolean string flags."""
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class LLMSettings(BaseModel):
    """Large language model configuration settings."""

    default_provider: str = Field(default="anthropic")
    default_temperature: float = Field(default=0.2)
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None

    model_config = {"str_strip_whitespace": True}

    allowed_providers: ClassVar[Set[str]] = {"anthropic", "openai", "ollama"}

    @field_validator("default_provider")
    @classmethod
    def check_provider(cls, provider: str) -> str:
        provider_lower = provider.lower()
        if provider_lower not in cls.allowed_providers:
            raise ValueError(f"Unknown provider '{provider}'. Allowed: {sorted(cls.allowed_providers)}")
        return provider_lower

    def ensure_credentials(self) -> None:
        """Validate provider-specific credentials."""
        if self.default_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for default provider 'anthropic'")
        if self.default_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for default provider 'openai'")
        if self.default_provider == "ollama" and not self.ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL is required for default provider 'ollama'")

    def provider_kwargs(self) -> Dict[str, Optional[str]]:
        """Return kwargs for instantiating the configured provider."""
        provider = self.default_provider
        kwargs: Dict[str, Optional[str]] = {"model": None, "temperature": self.default_temperature}
        if provider == "anthropic":
            kwargs["api_key"] = self.anthropic_api_key
            kwargs["model"] = self.anthropic_model
        elif provider == "openai":
            kwargs["api_key"] = self.openai_api_key
            kwargs["model"] = self.openai_model
        elif provider == "ollama":
            kwargs["base_url"] = self.ollama_base_url
            kwargs["model"] = self.ollama_model
        return kwargs


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    database_path: Path = Field(default=Path("data/Iiams.rmtree"))
    sqlite_extension_path: Path = Field(default=Path("./sqlite-extension/icu.dylib"))

    @field_validator("database_path", "sqlite_extension_path")
    @classmethod
    def expand_path(cls, value: Path) -> Path:
        return value.expanduser().resolve()


class OutputSettings(BaseModel):
    """Output directory settings."""

    output_dir: Path = Field(default=Path("output"))
    export_dir: Path = Field(default=Path("exports"))

    @field_validator("output_dir", "export_dir")
    @classmethod
    def expand_path(cls, value: Path) -> Path:
        return value.expanduser().resolve()


class PrivacySettings(BaseModel):
    """Privacy safeguards."""

    respect_private_flag: bool = Field(default=True)
    apply_110_year_rule: bool = Field(default=True)


class CitationSettings(BaseModel):
    """Citation formatting preferences."""

    default_style: str = Field(default="footnote")

    allowed_styles: ClassVar[Set[str]] = {"footnote", "parenthetical", "narrative"}

    @field_validator("default_style")
    @classmethod
    def check_style(cls, style: str) -> str:
        style_lower = style.lower()
        if style_lower not in cls.allowed_styles:
            raise ValueError(f"Invalid citation style '{style}'. Allowed: {sorted(cls.allowed_styles)}")
        return style_lower


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    log_file: Path = Field(default=Path("rmtool.log"))

    @field_validator("level")
    @classmethod
    def normalize_level(cls, level: str) -> str:
        return level.upper()

    @field_validator("log_file")
    @classmethod
    def expand_path(cls, value: Path) -> Path:
        return value.expanduser().resolve()


class AppConfig(BaseModel):
    """Top-level application configuration."""

    llm: LLMSettings
    database: DatabaseSettings
    output: OutputSettings
    privacy: PrivacySettings
    citation: CitationSettings
    logging: LoggingSettings

    class Config:
        arbitrary_types_allowed = True

    def ensure_directories(self) -> None:
        """Create output directories as needed."""
        self.output.output_dir.mkdir(parents=True, exist_ok=True)
        self.output.export_dir.mkdir(parents=True, exist_ok=True)

    def build_provider(self) -> LLMProvider:
        """Instantiate the configured default LLM provider."""
        self.llm.ensure_credentials()
        provider_kwargs = {k: v for k, v in self.llm.provider_kwargs().items() if v is not None}
        return get_provider(self.llm.default_provider, **provider_kwargs)


def load_app_config(env_path: Optional[Path] = None, auto_create_dirs: bool = True) -> AppConfig:
    """
    Load application configuration.

    Args:
        env_path: Optional path to a .env file. Defaults to project root .env if present.
        auto_create_dirs: When True, create output/export directories.
    """
    if env_path is None:
        env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    try:
        llm_settings = LLMSettings(
            default_provider=_env("DEFAULT_LLM_PROVIDER", "anthropic"),
            default_temperature=float(_env("LLM_TEMPERATURE", "0.2")),
            anthropic_api_key=_env("ANTHROPIC_API_KEY"),
            anthropic_model=_env("ANTHROPIC_MODEL", "claude-3-5-sonnet-20250110"),
            openai_api_key=_env("OPENAI_API_KEY"),
            openai_model=_env("OPENAI_MODEL", "gpt-4o-mini"),
            ollama_base_url=_env("OLLAMA_BASE_URL"),
            ollama_model=_env("OLLAMA_MODEL", "llama3.1"),
        )

        database_settings = DatabaseSettings(
            database_path=Path(_env("RM_DATABASE_PATH", "data/Iiams.rmtree")),
            sqlite_extension_path=Path(_env("SQLITE_ICU_EXTENSION", "./sqlite-extension/icu.dylib")),
        )

        output_settings = OutputSettings(
            output_dir=Path(_env("OUTPUT_DIR", "output")),
            export_dir=Path(_env("EXPORT_DIR", "exports")),
        )

        privacy_settings = PrivacySettings(
            respect_private_flag=_parse_bool(_env("RESPECT_PRIVATE_FLAG", "true"), True),
            apply_110_year_rule=_parse_bool(_env("APPLY_110_YEAR_RULE", "true"), True),
        )

        citation_settings = CitationSettings(
            default_style=_env("DEFAULT_CITATION_STYLE", "footnote"),
        )

        logging_settings = LoggingSettings(
            level=_env("LOG_LEVEL", "INFO"),
            log_file=Path(_env("LOG_FILE", "rmtool.log")),
        )

        config = AppConfig(
            llm=llm_settings,
            database=database_settings,
            output=output_settings,
            privacy=privacy_settings,
            citation=citation_settings,
            logging=logging_settings,
        )
    except ValidationError as exc:
        raise LLMError(f"Configuration validation failed: {exc}") from exc

    if auto_create_dirs:
        config.ensure_directories()

    try:
        config.llm.ensure_credentials()
    except ValueError as exc:
        raise LLMError(str(exc)) from exc
    return config


__all__ = ["AppConfig", "load_app_config"]
