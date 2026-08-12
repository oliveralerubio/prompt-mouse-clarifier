# Prompt Mouse Clarifier

Local, conservative prompt clarification triggered from configurable mouse buttons.

> Rewrite rough prompts into precise technical prompts without inventing scope.

Inspired by the *clarity and terminology-compression* idea behind `pi-clarify`, but implemented as a standalone Python project. This repository does **not** install or bundle `pi-clarify`.

## What it does

- Select rough text in any Wayland application.
- Hold a configured mouse button.
- Rewrite the text with a local Ollama model or an OpenAI-compatible API.
- Preserve paths, URLs, numbers, commands, errors, restrictions, and acceptance criteria.
- Paste the result back for review; it never auto-submits to an agent.
- Configure button mappings and the active provider from a small Tkinter GUI.

## Providers

### Ollama (local, no API key)

```bash
ollama pull gemma4:latest
pmc clarify "Haz que la búsqueda espere hasta que el usuario deje de escribir."
```

### OpenAI-compatible APIs

The same adapter works with OpenAI, OpenRouter, Together, vLLM, LiteLLM, LM Studio and other compatible gateways. Add a provider to `~/.config/prompt-mouse-clarifier/config.json`:

```json
{
  "name": "openrouter",
  "kind": "openai",
  "base_url": "https://openrouter.ai/api/v1",
  "model": "openai/gpt-4o-mini",
  "api_key_env": "OPENROUTER_API_KEY",
  "timeout": 45.0
}
```

The key is read only from the named environment variable. Never commit API keys.

## Install

Python 3.11+ is required. The core has no mandatory third-party dependencies.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
# Linux mouse backend (optional):
python -m pip install -e '.[linux]'
```

## GUI and daemon

```bash
pmc gui
pmc config-path
pmc daemon
```

The GUI edits:

- active provider;
- button names such as `BTN_SIDE`, `BTN_EXTRA`, or `BTN_MIDDLE`;
- click action;
- hold action.

Available actions in the portable MVP are `none`, `clarify`, and `previous_window`. Grammar correction and dictation are deliberately not bundled because their implementations are OS-, microphone-, and provider-specific; they can be added as separate adapters without publishing anyone's personal scripts.

## Example

Input:

```text
Haz que la búsqueda espere hasta que el usuario deje de escribir antes de buscar.
```

Possible output:

```text
Implementa un debounce en la entrada de búsqueda.
```

Input:

```text
Modifica /tmp/prompt-demo, no instales dependencias nuevas y verifica 3 casos.
```

The literal-preservation guard rejects an output that loses `/tmp/prompt-demo`, the `3`, or the no-dependencies constraint when a concrete token can be checked.

## Linux/Wayland notes

The optional mouse backend uses `evdev` and `UInput`, `wl-paste`/`wl-copy`, and `ydotool`. It auto-discovers a mouse exposing `BTN_SIDE` and `BTN_EXTRA`; it does not hard-code `/dev/input/eventN`.

Device permissions may require a udev rule or running the daemon with access to `/dev/input`. Do not grant broad permissions without understanding the local security impact.

## Architecture

```text
Tkinter GUI / CLI
       │
       ├── JSON config (XDG_CONFIG_HOME)
       │
Mouse evdev → action dispatcher → Wayland selection → Clarifier → provider
                                                       ├── Ollama
                                                       └── OpenAI-compatible APIs
```

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m compileall -q src
```

## Scope and roadmap

This first public release intentionally keeps the core small. Future contributions can add:

- configurable external commands for grammar and dictation;
- device picker and button-capture UI;
- KDE/systemd integration templates;
- macOS and Windows input backends;
- semantic regression/evaluation fixtures.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please keep provider code isolated, avoid logging prompt contents or secrets, and add tests for behavior changes.

## License

MIT. See [LICENSE](LICENSE).
