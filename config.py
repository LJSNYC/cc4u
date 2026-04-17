import json
import os
from pathlib import Path

CONFIG_PATH = os.path.expanduser("~/.config/cc4u/config.json")


def default_config() -> dict:
    return {
        "user_name": "user",
        "theme": "tactical",
        "left_widgets":    ["clock", "git_status", "cost_tracker"],
        "right_widgets":   ["pomodoro", "cpu_memory"],
        "left_col_width":  16,
        "right_col_width": 16,
        "left_heights":    [1, 2, 1],
        "right_heights":   [2, 1],
        "behavior": {"pty_command": "claude"},
    }


def auto_layout(
    widget_types: list,
    pty_col: int = 2,
    pty_col_span: int = 8,
    grid_columns: int = 12,
) -> dict:
    """Distribute widget_types into left/right sidebar lists for the 3-column layout.

    Returns a dict with keys:
      left_widgets, right_widgets, left_col_width, right_col_width,
      left_heights, right_heights
    """
    extras = [t for t in widget_types if t != "pty_pane"]

    left_cols  = pty_col
    right_cols = grid_columns - pty_col - pty_col_span

    # Both sides zero = PTY fills full width (minimal preset).
    # If no sidebar widgets were selected, return a clean full-width layout.
    # If the user did select widgets despite choosing minimal, fall back to balanced.
    if left_cols == 0 and right_cols == 0:
        if not extras:
            return {
                "left_widgets":    [],
                "right_widgets":   [],
                "left_col_width":  0,
                "right_col_width": 0,
                "left_heights":    [],
                "right_heights":   [],
            }
        left_cols  = 2
        right_cols = 2

    if left_cols == 0:
        left_types  = []
        right_types = extras[:6]
    elif right_cols == 0:
        left_types  = extras[:6]
        right_types = []
    else:
        total = left_cols + right_cols
        left_count  = min(6, round(len(extras) * left_cols / total))
        right_count = min(6, len(extras) - left_count)
        left_types  = extras[:left_count]
        right_types = extras[left_count:left_count + right_count]

    left_col_width  = max(8, min(40, round(left_cols  / grid_columns * 100)))
    right_col_width = max(8, min(40, round(right_cols / grid_columns * 100)))

    left_heights  = [1] * len(left_types)
    right_heights = [1] * len(right_types)

    return {
        "left_widgets":    left_types,
        "right_widgets":   right_types,
        "left_col_width":  left_col_width,
        "right_col_width": right_col_width,
        "left_heights":    left_heights,
        "right_heights":   right_heights,
    }


def _migrate_old_widgets(data: dict) -> dict:
    """Convert old grid-based config (with 'widgets' key) to new 3-column schema."""
    widgets = data.get("widgets", [])
    grid_columns = data.get("grid_columns", 12)

    # Find the pty_pane entry
    pty = next((w for w in widgets if w.get("type") == "pty_pane"), None)
    pty_col      = pty.get("col", 2)       if pty else 2
    pty_col_span = pty.get("col_span", 8)  if pty else 8

    # Left sidebar: entries left of pty, sorted by row
    left_entries = sorted(
        [w for w in widgets if w.get("type") != "pty_pane" and w.get("col", 0) < pty_col],
        key=lambda w: w.get("row", 0),
    )
    # Right sidebar: entries right of pty, sorted by row
    right_start = pty_col + pty_col_span
    right_entries = sorted(
        [w for w in widgets if w.get("type") != "pty_pane" and w.get("col", 0) >= right_start],
        key=lambda w: w.get("row", 0),
    )

    left_widgets  = [w["type"] for w in left_entries]
    right_widgets = [w["type"] for w in right_entries]

    left_cols  = pty_col
    right_cols = grid_columns - pty_col - pty_col_span

    left_col_width  = max(8, min(40, round(left_cols  / grid_columns * 100))) if left_cols  > 0 else 16
    right_col_width = max(8, min(40, round(right_cols / grid_columns * 100))) if right_cols > 0 else 16

    left_heights  = [1] * len(left_widgets)
    right_heights = [1] * len(right_widgets)

    # Remove old keys
    for key in ("widgets", "grid_columns", "grid_rows", "background_pattern"):
        data.pop(key, None)

    data.update({
        "left_widgets":    left_widgets,
        "right_widgets":   right_widgets,
        "left_col_width":  left_col_width,
        "right_col_width": right_col_width,
        "left_heights":    left_heights,
        "right_heights":   right_heights,
    })
    return data


def load() -> dict:
    path = Path(CONFIG_PATH)
    if not path.exists():
        return default_config()
    try:
        with open(path) as f:
            data = json.load(f)

        # Migrate old grid-based format if needed
        if "widgets" in data:
            data = _migrate_old_widgets(data)

        # Fill in any missing keys from defaults
        defaults = default_config()
        for k, v in defaults.items():
            data.setdefault(k, v)

        # Clamp column widths
        data["left_col_width"]  = max(8, min(40, data["left_col_width"]))
        data["right_col_width"] = max(8, min(40, data["right_col_width"]))

        # Fix height lists if lengths don't match widget lists
        if len(data["left_heights"]) != len(data["left_widgets"]):
            data["left_heights"] = [1] * len(data["left_widgets"])
        if len(data["right_heights"]) != len(data["right_widgets"]):
            data["right_heights"] = [1] * len(data["right_widgets"])

        return data
    except Exception:
        return default_config()


def save(data: dict) -> None:
    path = Path(CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.rename(path)
