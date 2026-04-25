from __future__ import annotations

import datetime as dt
import json
import threading
import time

import requests

import config

_PRAYER_NAMES = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

_lock = threading.Lock()
_cache = {"conf": None, "fetched_at": 0.0}


def _extract_conf_data(html: str) -> dict:
    idx = html.find("let confData")
    if idx < 0:
        raise RuntimeError("confData not found in mosque page HTML")
    start = html.find("{", idx)
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(html):
        c = html[i]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start : i + 1])
        i += 1
    raise RuntimeError("confData JSON object did not terminate")


def _refresh() -> dict:
    r = requests.get(config.MOSQUE_URL, headers={"User-Agent": "BerlinScreen/1.0"}, timeout=20)
    r.raise_for_status()
    conf = _extract_conf_data(r.text)
    with _lock:
        _cache["conf"] = conf
        _cache["fetched_at"] = time.time()
    return conf


def _get_conf() -> dict:
    with _lock:
        conf = _cache["conf"]
        age = time.time() - _cache["fetched_at"]
    if conf is None or age > config.PRAYER_CACHE_SECONDS:
        conf = _refresh()
    return conf


def _today_from_calendar(conf: dict, today: dt.date) -> list[str]:
    month = conf["calendar"][today.month - 1]
    # calendar day entries are [Fajr, Shuruq, Dhuhr, Asr, Maghrib, Isha]
    row = month[str(today.day)]
    return list(row)


def _today_iqama(conf: dict, today: dt.date) -> list[str]:
    month = conf["iqamaCalendar"][today.month - 1]
    row = month[str(today.day)]
    return list(row)


def _apply_offset(hhmm: str, offset: str) -> str:
    h, m = map(int, hhmm.split(":"))
    offset = offset.strip()
    sign = 1
    if offset.startswith("+"):
        offset = offset[1:]
    elif offset.startswith("-"):
        sign = -1
        offset = offset[1:]
    total = h * 60 + m + sign * int(offset)
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def snapshot(today: dt.date | None = None) -> dict:
    if today is None:
        today = dt.datetime.now().date()
    conf = _get_conf()
    cal = _today_from_calendar(conf, today)
    fajr, shuruq, dhuhr, asr, maghrib, isha = cal
    adhan = {
        "fajr": fajr, "shuruq": shuruq, "dhuhr": dhuhr,
        "asr": asr, "maghrib": maghrib, "isha": isha,
    }
    iqama_offsets = _today_iqama(conf, today)  # for 5 prayers, no shuruq
    iqama = {}
    for name, base, off in zip(_PRAYER_NAMES, [fajr, dhuhr, asr, maghrib, isha], iqama_offsets):
        iqama[name] = _apply_offset(base, off)

    is_friday = today.weekday() == 4
    jumua = None
    if is_friday:
        jumua = [t for t in [conf.get("jumua"), conf.get("jumua2"), conf.get("jumua3")] if t]

    return {
        "date": today.isoformat(),
        "mosque": conf.get("label") or conf.get("name"),
        "timezone": conf.get("timezone"),
        "adhan": adhan,
        "iqama": iqama,
        "jumua": jumua,
        "hijri_adjustment": conf.get("hijriAdjustment", 0),
    }


def prayer_times_for(today: dt.date) -> list[tuple[str, str]]:
    """Return list of (prayer_name, 'HH:MM') for today's 5 adhan times, in order."""
    snap = snapshot(today)
    return [(name, snap["adhan"][name]) for name in _PRAYER_NAMES]
