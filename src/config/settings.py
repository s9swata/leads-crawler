"""Settings management using Pydantic."""

import json
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for lead-gen CLI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    serper_api_key: Optional[str] = None
    crawl4ai_timeout: int = 30
    requests_per_second: float = 1.0
    respect_robots_txt: bool = True
    output_format: str = "csv"

    @classmethod
    def from_file(cls, file_path: str | Path) -> "Settings":
        """Load settings from a YAML or JSON file.

        Args:
            file_path: Path to config file (YAML or JSON)

        Returns:
            Settings instance with loaded configuration
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        if path.suffix in (".yaml", ".yml"):
            data: dict[str, Any] = yaml.safe_load(content) or {}
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        return cls(**data)

    @classmethod
    def from_path(cls, config_path: Optional[str | Path] = None) -> "Settings":
        """Load settings from file path or environment variables.

        File path (YAML/JSON) takes precedence over environment variables.

        Args:
            config_path: Optional path to config file

        Returns:
            Settings instance with configuration
        """
        if config_path:
            return cls.from_file(config_path)
        return cls()


__all__ = ["Settings"]
