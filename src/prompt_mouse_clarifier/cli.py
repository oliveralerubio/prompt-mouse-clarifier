"""Command-line entry points."""

from __future__ import annotations

import argparse
import sys

from .clarifier import Clarifier
from .config import config_path, load
from .mouse import EvdevMouseDaemon
from .providers import providers_from_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pmc")
    parser.add_argument("command", choices=["clarify", "daemon", "gui", "config-path"])
    parser.add_argument("text", nargs="*")
    args = parser.parse_args(argv)
    data = load()
    if args.command == "config-path":
        print(config_path())
        return 0
    if args.command == "clarify":
        text = " ".join(args.text) or sys.stdin.read()
        settings = data["settings"]
        try:
            result, provider = Clarifier(
                providers_from_dict(data["providers"]), settings["active_provider"]
            ).clarify(text)
        except Exception as exc:
            print(f"pmc: {exc}", file=sys.stderr)
            return 1
        print(result)
        print(f"# provider: {provider}", file=sys.stderr)
        return 0
    if args.command == "daemon":
        clarifier = Clarifier(
            providers_from_dict(data["providers"]),
            data["settings"]["active_provider"],
        )
        EvdevMouseDaemon(data, clarifier).run()
        return 0
    from .gui import run
    run()
    return 0
