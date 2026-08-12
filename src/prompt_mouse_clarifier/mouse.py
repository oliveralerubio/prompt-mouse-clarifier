"""Optional Linux evdev/UInput mouse backend."""

from __future__ import annotations

import subprocess
import time
from threading import Lock

from .clipboard import paste, restore_clipboard, selected_text
from .clarifier import Clarifier
from .prompt import validate_input

ACTIONS = {"none", "clarify", "previous_window"}


def previous_window() -> None:
    subprocess.run(["ydotool", "key", "56:1", "15:1", "15:0", "56:0"], check=False)


class EvdevMouseDaemon:
    def __init__(self, config: dict, clarifier: Clarifier):
        self.config = config
        self.clarifier = clarifier
        self.lock = Lock()

    def run(self) -> None:
        try:
            from evdev import InputDevice, UInput, ecodes, list_devices
        except ImportError as exc:
            raise RuntimeError("Install the optional Linux backend with: pip install 'prompt-mouse-clarifier[linux]'") from exc

        physical = self._find_device(InputDevice, list_devices, ecodes)
        virtual = UInput.from_device(physical, filtered_types=(ecodes.EV_SYN, ecodes.EV_FF), name="Prompt Mouse Clarifier")
        bindings = {item["button"]: item for item in self.config["settings"]["bindings"]}
        button_codes: dict[int, tuple[str, dict]] = {}
        for name, binding in bindings.items():
            code = getattr(ecodes, name, None)
            if code is not None:
                button_codes[code] = (name, binding)
        pressed: dict[int, float] = {}
        try:
            physical.grab()
            for event in physical.read_loop():
                if event.type == ecodes.EV_KEY and event.code in button_codes:
                    _name, binding = button_codes[event.code]
                    if event.value == 1:
                        pressed[event.code] = time.monotonic()
                    elif event.value == 0:
                        duration = time.monotonic() - pressed.pop(event.code, time.monotonic())
                        action = binding["hold"] if duration >= binding.get("hold_seconds", 0.35) else binding["click"]
                        self.dispatch(action)
                    continue
                virtual.write_event(event)
        finally:
            try:
                physical.ungrab()
            except OSError:
                pass
            virtual.close()
            physical.close()

    def _find_device(self, InputDevice, list_devices, ecodes):
        requested = self.config["settings"].get("input_device", "auto")
        for item in list_devices():
            device = InputDevice(item)
            caps = device.capabilities()
            if requested != "auto" and item != requested and getattr(device, "name", "") != requested:
                device.close()
                continue
            keys = set(caps.get(ecodes.EV_KEY, []))
            if ecodes.BTN_SIDE in keys and ecodes.BTN_EXTRA in keys and ecodes.EV_REL in caps:
                return device
            device.close()
        raise RuntimeError("No compatible mouse with BTN_SIDE and BTN_EXTRA was found")

    def dispatch(self, action: str) -> None:
        if action not in ACTIONS:
            raise ValueError(f"Unknown action: {action}")
        if action == "previous_window":
            previous_window()
            return
        if action == "none":
            return
        if not self.lock.acquire(blocking=False):
            return
        previous_clipboard = ""
        should_restore_clipboard = False
        try:
            text, previous = selected_text()
            previous_clipboard = previous
            should_restore_clipboard = bool(previous)
            validate_input(text)
            result, _provider = self.clarifier.clarify(text)
            if result != text:
                paste(result)
        except Exception:
            if should_restore_clipboard and previous_clipboard:
                restore_clipboard(previous_clipboard)
            raise
        else:
            if should_restore_clipboard and previous_clipboard:
                restore_clipboard(previous_clipboard)
        finally:
            self.lock.release()
