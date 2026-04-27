"""Facility status — elevator and escalator outages.

Aggregates per-line counts for U-Bahn and per-station counts for S-Bahn.

Data sources:
- S-Bahn: Deutsche Bahn FaSta API (https://developers.deutschebahn.com).
  Requires DB_FASTA_API_KEY in the environment. Reliable, well-documented.
- U-Bahn: NOT YET CONNECTED. As of 2026-04 there is no clean JSON
  endpoint published by BVG. The historical RSS feed and the BrokenLifts
  API both went away or were never JSON in the first place. See the
  _fetch_ubahn() docstring for the options we evaluated; if you find a
  reliable source, plug it in there and the rest works.
"""
from __future__ import annotations

import threading
import time

import requests

import config

_FASTA_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/fasta/v2/facilities"

_lock = threading.Lock()
_cache: dict = {"data": None, "fetched_at": 0.0}


def _fetch_sbahn() -> tuple[list, list]:
    """Returns (per-station entries, errors)."""
    if not config.DB_FASTA_API_KEY or not config.DB_CLIENT_ID:
        return (
            [{"station": s["name"], "outages": None} for s in config.WATCHED_SBAHN_STATIONS],
            ["sbahn: DB_CLIENT_ID and/or DB_FASTA_API_KEY not configured"],
        )

    station_numbers = ",".join(str(s["station_number"]) for s in config.WATCHED_SBAHN_STATIONS)
    headers = {
        "Accept": "application/json",
        "DB-Client-Id": config.DB_CLIENT_ID,
        "DB-Api-Key": config.DB_FASTA_API_KEY,
    }
    params = {"type": "ESCALATOR,ELEVATOR", "stationnumbers": station_numbers}

    try:
        r = requests.get(_FASTA_URL, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        body = r.json()
    except requests.RequestException as e:
        return (
            [{"station": s["name"], "outages": None} for s in config.WATCHED_SBAHN_STATIONS],
            [f"sbahn: {e}"],
        )

    facilities = body.get("facilities") if isinstance(body, dict) else body
    facilities = facilities or []

    counts: dict[int, int] = {s["station_number"]: 0 for s in config.WATCHED_SBAHN_STATIONS}
    for f in facilities:
        station = f.get("stationnumber")
        state = (f.get("state") or "").upper()
        if state == "INACTIVE" and station in counts:
            counts[station] += 1

    out = [
        {"station": s["name"], "outages": counts[s["station_number"]]}
        for s in config.WATCHED_SBAHN_STATIONS
    ]
    return out, []


def _fetch_ubahn() -> tuple[list, list]:
    """Returns (per-line entries, errors).

    No working public JSON source for BVG U-Bahn elevator/escalator status
    has been identified at the time of writing. Probed and ruled out:

    - bvg.de/api/aufzuege, /api/lifts, /de/Fahrinformationen/* — all 404
      via Next.js SPA shell.
    - BrokenLifts.org — server-rendered HTML; their old API surface no
      longer responds with JSON.
    - bvg.de/Aufzugsmeldungen.rss — 403, decommissioned.

    Returns line entries with `outages: None` so the frontend can render
    a placeholder ('—') without crashing.
    """
    return (
        [{"line": line.strip(), "outages": None} for line in config.WATCHED_LINES if line.strip()],
        ["ubahn: no public data source available"],
    )


def _fetch_all() -> dict:
    sbahn_data, sbahn_errors = _fetch_sbahn()
    ubahn_data, ubahn_errors = _fetch_ubahn()
    return {
        "ubahn": ubahn_data,
        "sbahn": sbahn_data,
        "fetched_at": time.time(),
        "errors": sbahn_errors + ubahn_errors,
    }


def snapshot() -> dict:
    with _lock:
        data = _cache["data"]
        age = time.time() - _cache["fetched_at"]
    if data is None or age > config.FACILITY_CACHE_SECONDS:
        data = _fetch_all()
        with _lock:
            _cache["data"] = data
            _cache["fetched_at"] = time.time()
    return data
