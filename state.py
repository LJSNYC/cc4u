import json
import time
from pathlib import Path

STATE_DIR = "/tmp/cc4u"

_cache: dict = {}
_cache_ts: dict = {}
_CACHE_TTL = 1.0  # seconds


def _read_json(filename: str, fallback):
    path = Path(STATE_DIR) / filename
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return fallback


def _cached_read(key: str, filename: str, fallback):
    now = time.monotonic()
    if key in _cache and now - _cache_ts.get(key, 0.0) < _CACHE_TTL:
        return _cache[key]
    result = _read_json(filename, fallback)
    _cache[key] = result
    _cache_ts[key] = now
    return result


def session() -> dict:
    return _cached_read("session", "session.json", {})


def git() -> dict:
    return _cached_read("git", "git.json", {})


def tools() -> list:
    data = _cached_read("tools", "tools.json", [])
    return data if isinstance(data, list) else []


WIDGET_DATA_DIR = str(Path.home() / ".config" / "cc4u" / "widget_data")


def widget_data_path(widget_type: str) -> Path:
    base = Path(WIDGET_DATA_DIR)
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{widget_type}.json"


def load_widget_data(widget_type: str) -> dict:
    path = widget_data_path(widget_type)
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_widget_data(widget_type: str, data: dict) -> None:
    path = widget_data_path(widget_type)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(path)
