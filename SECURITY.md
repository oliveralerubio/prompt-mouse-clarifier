# Security Policy

## Scope

Prompt Mouse Clarifier reads selected text, sends it to the provider configured by the user, and can paste the returned text. It does not submit prompts to another application automatically.

The Linux mouse backend requires access to input devices and uses `wl-paste`, `wl-copy`, and `ydotool`. Review those permissions before enabling the daemon.

## Reporting a vulnerability

Please do not open a public issue for a credential leak, arbitrary command execution, clipboard disclosure, or input-device permission bypass. Contact the maintainer through the private security contact available on the GitHub profile and include:

- affected version or commit;
- operating system and backend;
- minimal reproduction without secrets or personal clipboard contents;
- impact and any proposed mitigation.

Do not include API keys, access tokens, private prompts, or personal paths in the report.

## Security design

- Provider API keys are referenced by environment-variable name; they are not stored in the JSON configuration.
- Provider URLs must be HTTP(S) URLs without embedded credentials or query parameters.
- The core uses an argument list for subprocesses and does not execute provider or button values as shell commands.
- Concrete prompt details are checked before output is pasted.
- Failed copy-based selection restores the previous clipboard when possible.
- Cloud providers are skipped when their configured API-key environment variable is absent.
- Logs and error messages must not print prompt contents, clipboard contents, headers, or secret values.

Security is defense in depth, not a guarantee that a remote model will preserve every semantic detail. Review the rewritten prompt before sending it anywhere.
