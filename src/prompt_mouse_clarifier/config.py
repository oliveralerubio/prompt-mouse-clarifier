"""JSON configuration with safe defaults and XDG support."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


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
        Binding("BTN_EXTRA", click="none", hold="none"),
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
    return {"providers": deepcopy(DEFAULT_PROVIDERS), "settings": asdict(Settings())}


def load(path: Path | None = None) -> dict:
    path = path or config_path()
    if not path.exists():
        return default_config()
    data = json.loads(path.read_text())
    validate(data)
    return data


def save(data: dict, path: Path | None = None) -> Path:
    validate(data)
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def validate(data: dict) -> None:
    """Reject unsafe or unusable configuration before the daemon starts."""
    providers = data.get("providers")
    settings = data.get("settings")
    if not isinstance(providers, list) or not isinstance(settings, dict):
        raise ValueError("config requires providers[] and settings")
    names = set()
    for provider in providers:
        required = ("name", "kind", "base_url", "model")
        if not all(provider.get(key) for key in required):
            raise ValueError("each provider needs name, kind, base_url, and model")
        if provider["name"] in names:
            raise ValueError(f"duplicate provider name: {provider['name']}")
        names.add(provider["name"])
        if provider["kind"] not in {"ollama", "openai"}:
            raise ValueError(f"unsupported provider kind: {provider['kind']}")
        parsed = urlsplit(provider["base_url"])
        if parsed.username or parsed.password or parsed.query:
            raise ValueError(f"provider URL must not contain credentials or query parameters: {provider['name']}")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"provider URL must be an http(s) URL: {provider['name']}")
    active = settings.get("active_provider")
    if active and active not in names:
        raise ValueError(f"active provider does not exist: {active}")
    actions = {"none", "clarify", "previous_window"}
    for binding in settings.get("bindings", []):
        if not binding.get("button"):
            raise ValueError("binding button cannot be empty")
        if binding.get("click") not in actions or binding.get("hold") not in actions:
            raise ValueError("binding contains an unsupported action")
