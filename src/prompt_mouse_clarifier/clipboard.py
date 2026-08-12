"""Wayland selection and clipboard operations."""

from __future__ import annotations

import subprocess
import time


def selected_text() -> tuple[str, str]:
    """Return selected text and previous clipboard; never expose secrets in logs."""
    try:
        primary = subprocess.run(
            ["wl-paste", "--primary"], capture_output=True, text=True, timeout=1
        ).stdout.strip()
        if len(primary) >= 2:
            return primary, ""
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        previous = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=1).stdout
        subprocess.run(["ydotool", "key", "29:1", "46:1", "46:0", "29:0"], timeout=2)
        time.sleep(0.15)
        copied = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=1).stdout
        return copied.strip(), previous
    except (OSError, subprocess.SubprocessError):
        return "", ""


def paste(text: str) -> None:
    subprocess.run(["wl-copy", text], check=True, timeout=2)
    time.sleep(0.08)
    subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=True, timeout=2)
