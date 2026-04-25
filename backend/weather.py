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


def _fetch() -> dict:
    params = {
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m",
        "hourly": "temperature_2m,weather_code",
        "forecast_hours": 12,
        "timezone": config.TIMEZONE,
    }
    r = requests.get(_URL, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()
    cur = raw.get("current", {})
    hourly = raw.get("hourly", {})
    cur_desc, cur_icon = _wmo(cur.get("weather_code"))
    data = {
        "current": {
            "temp": cur.get("temperature_2m"),
            "code": cur.get("weather_code"),
            "description": cur_desc,
            "icon": cur_icon,
            "wind": cur.get("wind_speed_10m"),
            "humidity": cur.get("relative_humidity_2m"),
        },
        "hourly": [
            {
                "time": t,
                "temp": hourly.get("temperature_2m", [None])[i],
                "code": (hourly.get("weather_code") or [None])[i],
                "description": _wmo((hourly.get("weather_code") or [None])[i])[0],
                "icon":        _wmo((hourly.get("weather_code") or [None])[i])[1],
            }
            for i, t in enumerate(hourly.get("time", []))
        ],
    }
    return data


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
