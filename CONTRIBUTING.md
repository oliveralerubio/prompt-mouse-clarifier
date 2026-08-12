# Contributing

Thanks for helping improve Prompt Mouse Clarifier.

## Principles

- Keep the clarifier conservative: improve terminology and structure, do not invent scope.
- Do not log API keys, full prompts, clipboard contents, or audio.
- Keep provider integrations behind the `Provider` interface.
- Keep OS/input integrations optional and isolated from the prompt core.
- Add a regression test for each behavior change.

## Local checks

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m compileall -q src
```

## Pull requests

Describe the user-visible behavior, the providers/OSes affected, tests run, and any permissions required for input devices. Avoid bundling personal machine paths or service files in the public repository.
