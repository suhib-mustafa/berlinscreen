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

PRAYER_CACHE_SECONDS = 24 * 3600
WEATHER_CACHE_SECONDS = 600
TRANSIT_CACHE_SECONDS = 30

# Facility status (escalators / elevators).
# S-Bahn fetcher uses Deutsche Bahn's FaSta API — needs a free key from
# developers.deutschebahn.com; without it the S-Bahn entries return
# outages=None and the dashboard renders a placeholder.
# U-Bahn fetcher is currently a stub: BVG does not publish a clean JSON
# endpoint as of 2026-04, see backend/facility.py for the search history.
DB_FASTA_API_KEY = os.environ.get("DB_FASTA_API_KEY", "")
WATCHED_LINES = [s for s in os.environ.get("WATCHED_LINES", "U6,U7,U8").split(",") if s.strip()]
WATCHED_SBAHN_STATIONS = [
    {"name": "S-Wedding", "station_number": 8089137},
]
FACILITY_CACHE_SECONDS = 600  # 10 min — facility status changes slowly
