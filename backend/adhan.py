from __future__ import annotations

import datetime as dt
import os
import subprocess
import threading
import time

import config
import mawaqit

_fired: set[tuple[str, str]] = set()  # (date_iso, prayer_name)
_lock = threading.Lock()
_thread: threading.Thread | None = None


def _is_quiet_hour(hour: int) -> bool:
    start, end = config.QUIET_HOURS_START, config.QUIET_HOURS_END
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    # wraps midnight (e.g. 22..7)
    return hour >= start or hour < end


def _set_volume_for_now() -> None:
    hour = dt.datetime.now().hour
    pct = config.QUIET_VOLUME_PCT if _is_quiet_hour(hour) else config.NORMAL_VOLUME_PCT
    try:
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
            check=False, timeout=3,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # No PulseAudio/PipeWire here (e.g. Windows dev box) — playback proceeds
        # at whatever the OS-default volume is.
        pass


def _play():
    path = os.path.abspath(config.AUDIO_FILE)
    if not os.path.exists(path):
        print(f"[adhan] audio file missing at {path} — skipping playback")
        return
    _set_volume_for_now()
    cmd = list(config.AUDIO_CMD) + [path]
    try:
        subprocess.Popen(cmd)
    except FileNotFoundError:
        print(f"[adhan] audio command not found: {cmd}")


def play_now():
    """Synchronous test trigger — fires the Adhan immediately, regardless of time."""
    _play()


def _tick():
    now = dt.datetime.now()
    today_iso = now.date().isoformat()
    hhmm = now.strftime("%H:%M")
    try:
        times = mawaqit.prayer_times_for(now.date())
    except Exception as e:
        print(f"[adhan] could not load prayer times: {e}")
        return
    for name, t in times:
        if name == "fajr" and not config.ADHAN_FAJR_ENABLED:
            continue
        if t != hhmm:
            continue
        key = (today_iso, name)
        with _lock:
            if key in _fired:
                continue
            _fired.add(key)
        print(f"[adhan] firing {name} at {hhmm}")
        _play()


def _run():
    while True:
        try:
            _tick()
        except Exception as e:
            print(f"[adhan] tick error: {e}")
        # sleep to the top of the next minute
        now = dt.datetime.now()
        sleep_s = 60 - now.second + 1
        time.sleep(sleep_s)


def start():
    global _thread
    if _thread is not None:
        return
    _thread = threading.Thread(target=_run, name="adhan-scheduler", daemon=True)
    _thread.start()
