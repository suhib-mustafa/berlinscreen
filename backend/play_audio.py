"""Cross-platform audio file player. Used by the Adhan scheduler."""
from __future__ import annotations

import os
import platform
import subprocess
import sys


def play(path: str) -> int:
    if not os.path.exists(path):
        print(f"[play_audio] file not found: {path}", file=sys.stderr)
        return 2

    system = platform.system()

    if system == "Windows":
        import ctypes
        from ctypes import c_wchar_p

        mci = ctypes.windll.winmm
        alias = "berlinscreen_audio"

        def _send(cmd: str) -> int:
            return mci.mciSendStringW(c_wchar_p(cmd), None, 0, None)

        rc = _send(f'open "{path}" type mpegvideo alias {alias}')
        if rc != 0:
            buf = ctypes.create_unicode_buffer(256)
            mci.mciGetErrorStringW(rc, buf, 256)
            print(f"[play_audio] MCI open failed ({rc}): {buf.value}", file=sys.stderr)
            return rc
        try:
            _send(f"play {alias} wait")
        finally:
            _send(f"close {alias}")
        return 0

    if system == "Darwin":
        return subprocess.run(["afplay", path]).returncode

    # Linux (Pi). Try a few players.
    for cmd in (
        ["mpg123", "-q", path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        ["paplay", path],
        ["aplay", "-q", path],
    ):
        try:
            return subprocess.run(cmd).returncode
        except FileNotFoundError:
            continue

    print("[play_audio] no audio player found on Linux (tried mpg123, ffplay, paplay, aplay)", file=sys.stderr)
    return 3


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: play_audio.py <file>", file=sys.stderr)
        sys.exit(1)
    sys.exit(play(sys.argv[1]))
