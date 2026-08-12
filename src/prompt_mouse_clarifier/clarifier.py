"""Provider-independent prompt clarifier."""

from __future__ import annotations

from .prompt import PROMPT_SYSTEM, is_usable, normalize_result, validate_input
from .providers import Provider


class Clarifier:
    def __init__(self, providers: list[Provider], active: str):
        self.providers = providers
        self.active = active

    def clarify(self, text: str) -> tuple[str, str]:
        validate_input(text)
        ordered = sorted(self.providers, key=lambda p: p.name != self.active)
        failures: list[str] = []
        for provider in ordered:
            try:
                result = normalize_result(provider.complete(PROMPT_SYSTEM, text))
                if is_usable(text, result):
                    return result, provider.name
                failures.append(f"{provider.name}: unsafe or empty output")
            except Exception as exc:
                failures.append(f"{provider.name}: {exc}")
        raise RuntimeError("All providers failed: " + " | ".join(failures))
