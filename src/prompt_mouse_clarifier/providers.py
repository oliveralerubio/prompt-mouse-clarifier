"""Small dependency-free providers for Ollama and OpenAI-compatible APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Provider:
    name: str
    kind: str
    base_url: str
    model: str
    api_key_env: str = ""
    timeout: float = 45.0

    def complete(self, system: str, user: str) -> str:
        if self.kind == "ollama":
            return self._ollama(system, user)
        return self._openai_compatible(system, user)

    def _request(self, path: str, payload: dict, headers: dict[str, str]) -> dict:
        url = self.base_url.rstrip("/") + path
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise RuntimeError(f"{self.name} returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"{self.name} request failed: {exc}") from exc

    def _ollama(self, system: str, user: str) -> str:
        data = self._request(
            "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "options": {"temperature": 0.2},
            },
            {},
        )
        return str(data.get("message", {}).get("content", "")).strip()

    def _openai_compatible(self, system: str, user: str) -> str:
        key = os.environ.get(self.api_key_env, "") if self.api_key_env else ""
        if self.api_key_env and not key:
            raise RuntimeError(f"missing API key environment variable: {self.api_key_env}")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        data = self._request(
            "/chat/completions",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            headers,
        )
        return str(data.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()


def providers_from_dict(items: list[dict]) -> list[Provider]:
    return [Provider(**item) for item in items]
