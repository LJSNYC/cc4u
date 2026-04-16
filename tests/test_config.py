import json
import pytest
import config


# ── auto_layout ───────────────────────────────────────────────────────────────

def test_auto_layout_balanced_returns_dict():
    """auto_layout returns a dict with all required keys and correct widths."""
    result = config.auto_layout(
        ["pty_pane", "clock", "git_status"],
        pty_col=2,
        pty_col_span=8,
    )
    assert isinstance(result, dict)
    for key in ("left_widgets", "right_widgets", "left_col_width", "right_col_width",
                "left_heights", "right_heights"):
        assert key in result, f"missing key: {key}"
    # 2/12 * 100 = 16.67 → round() = 17
    assert result["left_col_width"]  == 17
    assert result["right_col_width"] == 17


def test_auto_layout_no_pty():
    """auto_layout without pty_pane puts items in left_widgets."""
    result = config.auto_layout(["clock", "git_status"])
    assert len(result["left_widgets"]) > 0
    assert len(result["left_heights"]) == len(result["left_widgets"])


def test_auto_layout_heights_match_widgets():
    """Heights lists always match widget list lengths."""
    result = config.auto_layout(
        ["pty_pane", "clock", "git_status", "cost_tracker", "pomodoro"],
        pty_col=2,
        pty_col_span=8,
    )
    assert len(result["left_heights"])  == len(result["left_widgets"])
    assert len(result["right_heights"]) == len(result["right_widgets"])


def test_auto_layout_caps_at_6():
    """Each sidebar is capped at 6 widgets even with many extras."""
    many_extras = [f"w{i}" for i in range(20)]
    result = config.auto_layout(
        ["pty_pane"] + many_extras,
        pty_col=2,
        pty_col_span=8,
    )
    assert len(result["left_widgets"])  <= 6
    assert len(result["right_widgets"]) <= 6


def test_auto_layout_left_only_when_no_right_cols():
    """When right_cols == 0, all extras go to left sidebar."""
    result = config.auto_layout(
        ["pty_pane", "clock", "git_status"],
        pty_col=2,
        pty_col_span=10,  # 2 + 10 = 12, right_cols = 0
        grid_columns=12,
    )
    assert result["right_widgets"] == []
    assert "clock" in result["left_widgets"]


def test_auto_layout_right_only_when_no_left_cols():
    """When left_cols == 0, all extras go to right sidebar."""
    result = config.auto_layout(
        ["pty_pane", "clock", "git_status"],
        pty_col=0,
        pty_col_span=8,
        grid_columns=12,
    )
    assert result["left_widgets"] == []
    assert len(result["right_widgets"]) > 0


def test_auto_layout_both_zero_uses_default():
    """When pty fills the whole grid with no extras, sides still have valid (empty) lists."""
    result = config.auto_layout(
        ["pty_pane"],
        pty_col=0,
        pty_col_span=12,
        grid_columns=12,
    )
    assert result["left_widgets"]  == []
    assert result["right_widgets"] == []


# ── config load/save ──────────────────────────────────────────────────────────

def test_load_returns_default_when_missing(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(config_path))
    cfg = config.load()
    assert cfg["theme"] == "tactical"
    assert "left_widgets" in cfg
    assert isinstance(cfg["left_widgets"], list)


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(config_path))
    data = config.default_config()
    data["theme"] = "dracula"
    config.save(data)
    loaded = config.load()
    assert loaded["theme"] == "dracula"
    assert "left_widgets"   in loaded
    assert "left_col_width" in loaded


def test_save_is_atomic(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(config_path))
    config.save(config.default_config())
    assert config_path.exists()
    assert not (tmp_path / "config.json.tmp").exists()


def test_migrate_old_widgets(tmp_path, monkeypatch):
    """load() with old-format file (widgets key) produces new schema keys."""
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(config_path))

    old_data = {
        "user_name": "user",
        "theme": "tactical",
        "grid_columns": 12,
        "grid_rows": 6,
        "widgets": [
            {"type": "pty_pane",     "col": 2, "row": 0, "col_span": 8, "row_span": 6},
            {"type": "clock",        "col": 0, "row": 0, "col_span": 2, "row_span": 1},
            {"type": "git_status",   "col": 0, "row": 1, "col_span": 2, "row_span": 2},
            {"type": "pomodoro",     "col": 10, "row": 0, "col_span": 2, "row_span": 2},
        ],
        "behavior": {"pty_command": "claude"},
    }
    config_path.write_text(json.dumps(old_data))

    loaded = config.load()

    # Old keys should be gone
    assert "widgets"      not in loaded
    assert "grid_columns" not in loaded
    assert "grid_rows"    not in loaded

    # New keys should be present
    assert "left_widgets"    in loaded
    assert "right_widgets"   in loaded
    assert "left_col_width"  in loaded
    assert "right_col_width" in loaded
    assert "left_heights"    in loaded
    assert "right_heights"   in loaded

    # Left sidebar should have clock and git_status (col < 2)
    assert "clock"      in loaded["left_widgets"]
    assert "git_status" in loaded["left_widgets"]

    # Right sidebar should have pomodoro (col >= 10)
    assert "pomodoro" in loaded["right_widgets"]

    # Heights must match widget counts
    assert len(loaded["left_heights"])  == len(loaded["left_widgets"])
    assert len(loaded["right_heights"]) == len(loaded["right_widgets"])
