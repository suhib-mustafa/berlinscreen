"""Auto screen-off at night.

Runs a background thread that turns the Pi's connected display off between
SCREEN_OFF_HOUR and SCREEN_ON_HOUR (wrap-around aware). Tries vcgencmd first
(legacy / X11), falls back to wlr-randr (Wayland / labwc).
"""
from __future__ import annotations

import datetime as dt
import subprocess
import threading
import time

import config

_lock = threading.Lock()
_thread: threading.Thread | None = None
_last_applied: bool | None = None  # True = display was set off; False = on


def _is_off_hour(hour: int) -> bool:
    start, end = config.SCREEN_OFF_HOUR, config.SCREEN_ON_HOUR
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def _try_cmd(cmd: list[str]) -> bool:
    try:
        r = subprocess.run(
            cmd, check=False, timeout=5,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _set_display_power(on: bool) -> bool:
    """Try several mechanisms to turn the connected display on/off.

    Returns True if any of them succeeded.
    """
    if on:
        candidates = [
            ["vcgencmd", "display_power", "1"],
            ["wlr-randr", "--output", "HDMI-A-1", "--on"],
            ["wlr-randr", "--output", "HDMI-A-2", "--on"],
        ]
    else:
        candidates = [
            ["vcgencmd", "display_power", "0"],
            ["wlr-randr", "--output", "HDMI-A-1", "--off"],
            ["wlr-randr", "--output", "HDMI-A-2", "--off"],
        ]
    for cmd in candidates:
        if _try_cmd(cmd):
            return True
    return False


def _tick() -> None:
    global _last_applied
    if not config.SCREEN_CONTROL_ENABLED:
        return
    hour = dt.datetime.now().hour
    should_be_off = _is_off_hour(hour)
    with _lock:
        if _last_applied == should_be_off:
            return
    if _set_display_power(not should_be_off):
        with _lock:
            _last_applied = should_be_off
        print(f"[screen] display -> {'off' if should_be_off else 'on'} (hour={hour:02d})")
    else:
        # If no mechanism worked once, don't spam — try again next tick anyway.
        print(f"[screen] could not change display power (hour={hour:02d})")


def _run() -> None:
    while True:
        try:
            _tick()
        except Exception as e:
            print(f"[screen] tick error: {e}")
        now = dt.datetime.now()
        time.sleep(60 - now.second + 1)


def start() -> None:
    global _thread
    if _thread is not None:
        return
    if not config.SCREEN_CONTROL_ENABLED:
        print("[screen] disabled via SCREEN_CONTROL=0")
        return
    _thread = threading.Thread(target=_run, name="screen-scheduler", daemon=True)
    _thread.start()
