import json
from pathlib import Path

STATE_DIR = "/tmp/cc4u"


def _read_json(filename: str, fallback):
    path = Path(STATE_DIR) / filename
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return fallback


def session() -> dict:
    return _read_json("session.json", {})


def git() -> dict:
    return _read_json("git.json", {})


def tools() -> list:
    data = _read_json("tools.json", [])
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
