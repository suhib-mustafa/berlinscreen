import os
import shlex
import sys

# Load /project-root/.env if present, before any os.environ.get below.
# Optional — silently no-ops if python-dotenv isn't installed (e.g. on a
# minimal Pi setup) or if the .env file doesn't exist. The file is meant
# for laptop dev; on the Pi we use systemd's EnvironmentFile=/etc/berlinscreen.env.
try:
    from dotenv import load_dotenv
    _project_root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(_project_root_env):
        load_dotenv(_project_root_env)
except ImportError:
    pass

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

PRAYER_CACHE_SECONDS = 24 * 3600
WEATHER_CACHE_SECONDS = 600
TRANSIT_CACHE_SECONDS = 30
