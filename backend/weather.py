import datetime as dt
import threading
import time

import requests

import config

_URL = "https://api.open-meteo.com/v1/forecast"

_lock = threading.Lock()
_cache = {"data": None, "fetched_at": 0.0}

_WMO = {
    0: ("Clear",                    "☀"),
    1: ("Mainly clear",             "🌤"),
    2: ("Partly cloudy",            "⛅"),
    3: ("Overcast",                 "☁"),
    45: ("Fog",                     "🌫"),
    48: ("Fog",                     "🌫"),
    51: ("Light drizzle",           "🌦"),
    53: ("Drizzle",                 "🌦"),
    55: ("Heavy drizzle",           "🌧"),
    61: ("Light rain",              "🌦"),
    63: ("Rain",                    "🌧"),
    65: ("Heavy rain",              "🌧"),
    71: ("Light snow",              "🌨"),
    73: ("Snow",                    "❄"),
    75: ("Heavy snow",              "❄"),
    77: ("Snow grains",             "❄"),
    80: ("Rain showers",            "🌦"),
    81: ("Rain showers",            "🌧"),
    82: ("Heavy rain showers",      "🌧"),
    85: ("Snow showers",            "🌨"),
    86: ("Heavy snow showers",      "🌨"),
    95: ("Thunderstorm",            "⛈"),
    96: ("Thunderstorm w/ hail",    "⛈"),
    99: ("Thunderstorm w/ heavy hail", "⛈"),
}


def _wmo(code):
    desc, icon = _WMO.get(code, ("—", "•"))
    return desc, icon


_RAIN_MM_THRESHOLD = 0.1  # mm — anything below this is "trace", treat as dry


def _fetch() -> dict:
    params = {
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m",
        "hourly": "temperature_2m,weather_code,precipitation,precipitation_probability",
        "forecast_hours": 12,
        "timezone": config.TIMEZONE,
    }
    r = requests.get(_URL, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()
    cur = raw.get("current", {})
    hourly = raw.get("hourly", {})
    cur_desc, cur_icon = _wmo(cur.get("weather_code"))
    hourly_entries = [
        {
            "time": t,
            "temp": (hourly.get("temperature_2m") or [None])[i],
            "code": (hourly.get("weather_code") or [None])[i],
            "description": _wmo((hourly.get("weather_code") or [None])[i])[0],
            "icon":        _wmo((hourly.get("weather_code") or [None])[i])[1],
            "precipitation_mm": (hourly.get("precipitation") or [None])[i],
            "precipitation_probability": (hourly.get("precipitation_probability") or [None])[i],
        }
        for i, t in enumerate(hourly.get("time", []))
    ]
    data = {
        "current": {
            "temp": cur.get("temperature_2m"),
            "code": cur.get("weather_code"),
            "description": cur_desc,
            "icon": cur_icon,
            "wind": cur.get("wind_speed_10m"),
            "humidity": cur.get("relative_humidity_2m"),
        },
        "hourly": hourly_entries,
        "next_2h": _summarize_next_2h(hourly_entries),
    }
    return data


def _summarize_next_2h(hourly: list) -> dict:
    """Return {"mm": float, "max_probability": int, "summary": str} for the next ~2h."""
    now = dt.datetime.now()
    upcoming = []
    for h in hourly:
        try:
            ts = dt.datetime.fromisoformat(h["time"])
        except (KeyError, ValueError):
            continue
        if ts >= now.replace(minute=0, second=0, microsecond=0):
            upcoming.append((ts, h))
        if len(upcoming) >= 3:
            break

    if not upcoming:
        return {"mm": 0, "max_probability": 0, "summary": "—"}

    total_mm = sum((h.get("precipitation_mm") or 0) for _, h in upcoming)
    max_prob = max(((h.get("precipitation_probability") or 0) for _, h in upcoming), default=0)
    rain = [(ts, h) for ts, h in upcoming if (h.get("precipitation_mm") or 0) >= _RAIN_MM_THRESHOLD]

    if not rain:
        return {
            "mm": round(total_mm, 1),
            "max_probability": int(max_prob),
            "summary": "Dry next 2h",
        }

    first_ts, _ = rain[0]
    minutes = int(max(0, (first_ts - now).total_seconds() // 60))
    if minutes <= 10:
        summary = f"Rain now · {total_mm:.1f} mm next 2h"
    else:
        summary = f"Rain in ~{minutes} min · {total_mm:.1f} mm next 2h"
    return {
        "mm": round(total_mm, 1),
        "max_probability": int(max_prob),
        "summary": summary,
    }


def snapshot() -> dict:
    with _lock:
        data = _cache["data"]
        age = time.time() - _cache["fetched_at"]
    if data is None or age > config.WEATHER_CACHE_SECONDS:
        data = _fetch()
        with _lock:
            _cache["data"] = data
            _cache["fetched_at"] = time.time()
    return data
