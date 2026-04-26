import os
import shlex
import sys

MOSQUE_URL = "https://mawaqit.net/en/msjd-lzytwn-seituna-moschee-berlin-14059-germany"

LATITUDE = 52.5154748
LONGITUDE = 13.287296
TIMEZONE = "Europe/Berlin"

STOPS = [
    {"name": "U Afrikanische Str. → Alt-Mariendorf", "query": "U Afrikanische Str", "lines": ["U6"], "direction_contains": "Alt-Mariendorf"},
    {"name": "Kapweg → Osloer Str.",                 "query": "Kapweg, Berlin",   "lines": ["125", "128"], "direction_contains": "Osloer"},
    {"name": "Kurt-Schumacher-Platz → Jungfernheide", "query": "Kurt-Schumacher-Platz, Berlin", "lines": ["M21", "X21"], "direction_contains": "Jungfernheide"},
]

BVG_BASE = "https://v6.bvg.transport.rest"

AUDIO_FILE = os.environ.get("ADHAN_AUDIO", os.path.join(os.path.dirname(__file__), "..", "audio", "adhan.mp3"))

_env_cmd = os.environ.get("ADHAN_CMD")
if _env_cmd:
    AUDIO_CMD = shlex.split(_env_cmd)
else:
    AUDIO_CMD = [sys.executable, os.path.join(os.path.dirname(__file__), "play_audio.py")]

ADHAN_FAJR_ENABLED = os.environ.get("ADHAN_FAJR", "0") == "1"

# Smart Adhan volume: lower the system volume when the prayer falls within
# the configured quiet hours. End hour is exclusive (e.g. 22..7 = 22:00 inclusive
# through 06:59 inclusive). Values 0–100.
QUIET_HOURS_START = int(os.environ.get("QUIET_HOURS_START", "22"))
QUIET_HOURS_END = int(os.environ.get("QUIET_HOURS_END", "7"))
QUIET_VOLUME_PCT = int(os.environ.get("QUIET_VOLUME_PCT", "50"))
NORMAL_VOLUME_PCT = int(os.environ.get("NORMAL_VOLUME_PCT", "90"))

PRAYER_CACHE_SECONDS = 24 * 3600
WEATHER_CACHE_SECONDS = 600
TRANSIT_CACHE_SECONDS = 30

# Auto screen-off at night. The connected display is blanked between
# SCREEN_OFF_HOUR (inclusive) and SCREEN_ON_HOUR (exclusive); the wrap
# around midnight is handled. SCREEN_CONTROL_ENABLED=0 disables the feature.
SCREEN_CONTROL_ENABLED = os.environ.get("SCREEN_CONTROL", "1") == "1"
SCREEN_OFF_HOUR = int(os.environ.get("SCREEN_OFF_HOUR", "23"))
SCREEN_ON_HOUR = int(os.environ.get("SCREEN_ON_HOUR", "6"))
