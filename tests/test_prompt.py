from typing import cast

from prompt_mouse_clarifier.clarifier import Clarifier
from prompt_mouse_clarifier.config import default_config, load, save, validate
from prompt_mouse_clarifier.mouse import EvdevMouseDaemon
from prompt_mouse_clarifier.prompt import is_usable, normalize_result, validate_input
from prompt_mouse_clarifier.providers import Provider, providers_from_dict


def test_literals_survive_markdown_formatting():
    original = "Modifica /tmp/demo, usa 3 reintentos y conserva https://example.test/x."
    result = "Modifica `/tmp/demo`, usa 3 reintentos y conserva https://example.test/x."
    assert is_usable(original, result)


def test_missing_literal_is_rejected():
    original = "Modifica /tmp/demo y verifica 3 casos."
    assert not is_usable(original, "Modifica el proyecto y verifica algunos casos.")


def test_numeric_words_preserve_numeric_detail():
    assert is_usable("Verifica 3 casos.", "Verifica tres casos.")


def test_wrappers_are_removed():
    assert normalize_result("Prompt:\nHazlo") == "Hazlo"
    assert normalize_result("```text\nHazlo\n```") == "Hazlo"


def test_input_limits():
    validate_input("prompt")


def test_provider_fallback_and_active_preference():
    class FakeProvider(Provider):
        def __init__(self, name, response=None, error=None):
            super().__init__(name=name, kind="ollama", base_url="http://fake", model="fake")
            self.response: str = response or ""
            self.error = error

        def complete(self, system: str, user: str) -> str:
            if self.error:
                raise RuntimeError(self.error)
            return self.response

    original = "Modifica /tmp/demo y verifica 3 casos."
    clarifier = Clarifier(
        [
            FakeProvider("fallback", "Modifica `/tmp/demo` y verifica 3 casos."),
            FakeProvider("active", error="offline"),
        ],
        "active",
    )
    result, provider = clarifier.clarify(original)
    assert provider == "fallback"
    assert "/tmp/demo" in result


def test_config_round_trip(tmp_path):
    path = tmp_path / "config.json"
    data = default_config()
    data["settings"]["active_provider"] = "openai-compatible"
    save(data, path)
    assert load(path)["settings"]["active_provider"] == "openai-compatible"


def test_provider_schema_factory():
    items = [{"name": "local", "kind": "ollama", "base_url": "http://localhost", "model": "x"}]
    assert providers_from_dict(items)[0].name == "local"


def test_config_rejects_credentials_in_provider_url():
    data = default_config()
    data["providers"][0]["base_url"] = "https://user:secret@example.test/v1"
    try:
        validate(data)
    except ValueError as exc:
        assert "credentials" in str(exc)
    else:
        raise AssertionError("unsafe provider URL was accepted")


def test_default_config_only_uses_public_actions():
    actions = {"none", "clarify", "previous_window"}
    for binding in default_config()["settings"]["bindings"]:
        assert binding["click"] in actions
        assert binding["hold"] in actions


def test_copy_selection_failure_restores_clipboard(monkeypatch):
    import prompt_mouse_clarifier.mouse as mouse_module

    class FailingClarifier:
        def clarify(self, text):
            raise RuntimeError("provider offline")

    pasted = []
    restored = []
    monkeypatch.setattr(mouse_module, "selected_text", lambda: ("selected", "previous clipboard"))
    monkeypatch.setattr(mouse_module, "paste", lambda text: pasted.append(text))
    monkeypatch.setattr(mouse_module, "restore_clipboard", lambda text: restored.append(text))

    daemon = EvdevMouseDaemon(
        {"settings": {"bindings": []}}, cast(Clarifier, FailingClarifier())
    )
    try:
        daemon.dispatch("clarify")
    except RuntimeError as exc:
        assert str(exc) == "provider offline"
    else:
        raise AssertionError("provider failure was swallowed")
    assert pasted == []
    assert restored == ["previous clipboard"]


def test_copy_selection_success_restores_previous_clipboard(monkeypatch):
    import prompt_mouse_clarifier.mouse as mouse_module

    class SuccessfulClarifier:
        def clarify(self, text):
            return "rewritten", "fake"

    pasted = []
    restored = []
    monkeypatch.setattr(mouse_module, "selected_text", lambda: ("selected", "previous clipboard"))
    monkeypatch.setattr(mouse_module, "paste", lambda text: pasted.append(text))
    monkeypatch.setattr(mouse_module, "restore_clipboard", lambda text: restored.append(text))

    daemon = EvdevMouseDaemon(
        {"settings": {"bindings": []}}, cast(Clarifier, SuccessfulClarifier())
    )
    daemon.dispatch("clarify")
    assert pasted == ["rewritten"]
    assert restored == ["previous clipboard"]
