from __future__ import annotations

import datetime as dt
import threading
import time

import requests

import config

_lock = threading.Lock()
_stop_ids: dict[str, str] = {}
_dep_cache: dict[str, tuple[float, list[dict]]] = {}


def _resolve_stop_id(query: str) -> str | None:
    if query in _stop_ids:
        return _stop_ids[query]
    r = requests.get(
        f"{config.BVG_BASE}/locations",
        params={"query": query, "results": 5, "stops": "true", "addresses": "false", "poi": "false"},
        timeout=15,
    )
    r.raise_for_status()
    items = r.json()
    stop_id = None
    for item in items:
        if item.get("type") == "stop":
            stop_id = item.get("id")
            break
    if stop_id:
        _stop_ids[query] = stop_id
    return stop_id


def _fetch_departures(stop_id: str) -> list[dict]:
    r = requests.get(
        f"{config.BVG_BASE}/stops/{stop_id}/departures",
        params={"duration": 120, "results": 40},
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    return body.get("departures", [])


def _cached_departures(stop_id: str) -> list[dict]:
    now = time.time()
    with _lock:
        entry = _dep_cache.get(stop_id)
    if entry and now - entry[0] < config.TRANSIT_CACHE_SECONDS:
        return entry[1]
    deps = _fetch_departures(stop_id)
    with _lock:
        _dep_cache[stop_id] = (now, deps)
    return deps


def _minutes_until(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        when = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = dt.datetime.now(when.tzinfo)
    delta = (when - now).total_seconds()
    return int(delta // 60)


_DISRUPTION_TYPES = {"warning", "status"}

# Translation cache: German source string -> English translation. Keyed by the
# raw German since BVG repeats the same text across departures and across
# polling cycles. In-memory only — restart re-translates, which is fine.
_translation_cache: dict[str, str] = {}
_translation_lock = threading.Lock()


def _translate_de_to_en(text: str) -> str:
    """Translate via DeepL if configured; otherwise return the original.

    Failures (network, auth, rate-limit) silently fall back to the German
    source so a translation outage never blocks disruption rendering.
    """
    if not text or not config.DEEPL_API_KEY:
        return text
    with _translation_lock:
        cached = _translation_cache.get(text)
    if cached is not None:
        return cached

    # Free-tier keys end in ":fx" and use a different endpoint.
    is_free = config.DEEPL_API_KEY.endswith(":fx")
    url = (
        "https://api-free.deepl.com/v2/translate"
        if is_free
        else "https://api.deepl.com/v2/translate"
    )
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"DeepL-Auth-Key {config.DEEPL_API_KEY}"},
            data={"text": text, "target_lang": "EN"},
            timeout=8,
        )
        r.raise_for_status()
        translations = (r.json() or {}).get("translations") or []
        if translations:
            translated = translations[0].get("text") or text
            with _translation_lock:
                _translation_cache[text] = translated
            return translated
    except (requests.RequestException, ValueError):
        pass
    return text


def _extract_remarks(d: dict, line: str, seen: set, out: list) -> None:
    """Append unique disruption-style remarks from a departure into `out`.

    `seen` is a set of dedup keys reused across departures for one stop.
    """
    for r in (d.get("remarks") or []):
        rtype = r.get("type")
        if rtype not in _DISRUPTION_TYPES:
            continue
        summary = (r.get("summary") or r.get("text") or "").strip()
        if not summary:
            continue
        code = r.get("code") or ""
        key = (code, line, summary[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "line": line,
            "summary": _translate_de_to_en(summary),
            "code": code,
            "type": rtype,
        })


def _filter_and_shape(deps: list[dict], lines: list[str], direction_contains: str | None):
    departures = []
    seen_remarks: set = set()
    disruptions: list = []
    for d in deps:
        line = (d.get("line") or {}).get("name") or ""
        if line not in lines:
            continue
        # Collect disruption remarks even if direction is filtered out — they
        # apply to the line as a whole, not just the matching direction.
        _extract_remarks(d, line, seen_remarks, disruptions)
        direction = d.get("direction") or ""
        if direction_contains and direction_contains.lower() not in direction.lower():
            continue
        departures.append({
            "line": line,
            "direction": direction,
            "when": d.get("when"),
            "plannedWhen": d.get("plannedWhen"),
            "delay_seconds": d.get("delay"),
            "in_minutes": _minutes_until(d.get("when") or d.get("plannedWhen")),
            "cancelled": bool(d.get("cancelled")),
        })
    departures.sort(key=lambda x: (x["in_minutes"] is None, x["in_minutes"] if x["in_minutes"] is not None else 9999))
    return departures[:6], disruptions


def snapshot() -> list[dict]:
    out = []
    for stop in config.STOPS:
        entry = {"stop": stop["name"], "departures": [], "disruptions": [], "error": None}
        try:
            stop_id = _resolve_stop_id(stop["query"])
            if not stop_id:
                entry["error"] = "stop not found"
            else:
                deps = _cached_departures(stop_id)
                entry["departures"], entry["disruptions"] = _filter_and_shape(
                    deps, stop["lines"], stop.get("direction_contains"),
                )
        except requests.RequestException as e:
            entry["error"] = f"network: {e}"
        out.append(entry)
    return out
