"""JSON configuration with safe defaults and XDG support."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Binding:
    button: str
    click: str = "none"
    hold: str = "clarify"
    hold_seconds: float = 0.35


@dataclass
class Settings:
    active_provider: str = "ollama"
    bindings: list[Binding] = field(default_factory=lambda: [
        Binding("BTN_SIDE", click="previous_window", hold="clarify"),
        Binding("BTN_EXTRA", click="dictation", hold="grammar"),
    ])
    input_device: str = "auto"
    clipboard_backend: str = "wayland"


DEFAULT_PROVIDERS = [
    {
        "name": "ollama",
        "kind": "ollama",
        "base_url": "http://127.0.0.1:11434",
        "model": "gemma4:latest",
        "api_key_env": "",
        "timeout": 45.0,
    },
    {
        "name": "openai-compatible",
        "kind": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "timeout": 45.0,
    },
]


def config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "prompt-mouse-clarifier" / "config.json"


def default_config() -> dict:
    return {"providers": DEFAULT_PROVIDERS, "settings": asdict(Settings())}


def load(path: Path | None = None) -> dict:
    path = path or config_path()
    if not path.exists():
        return default_config()
    return json.loads(path.read_text())


def save(data: dict, path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path
