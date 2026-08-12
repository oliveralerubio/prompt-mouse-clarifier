from prompt_mouse_clarifier.clarifier import Clarifier
from prompt_mouse_clarifier.config import default_config, load, save
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
        [FakeProvider("fallback", "Modifica `/tmp/demo` y verifica 3 casos."), FakeProvider("active", error="offline")],
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
