from pathlib import Path
import pytest
import sys

# Add parent directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

import themes


def test_list_themes_returns_all_json_files():
    names = themes.list_themes()
    assert "tactical" in names
    assert "dracula" in names
    assert len(names) >= 18


def test_load_theme_returns_colors_dict():
    t = themes.load_theme("tactical")
    assert "bg_primary" in t["colors"]
    assert "border" in t["colors"]
    assert "accent_primary" in t["colors"]


def test_load_theme_raises_for_unknown():
    with pytest.raises(FileNotFoundError):
        themes.load_theme("does_not_exist")


def test_to_textual_theme_returns_theme_object():
    from textual.theme import Theme
    t = themes.to_textual_theme("tactical")
    assert isinstance(t, Theme)
    assert t.name == "tactical"
    assert t.background is not None
    assert "widget-border" in (t.variables or {})


def test_write_tcss_creates_marker_file(tmp_path):
    out_path = tmp_path / "theme.tcss"
    themes.write_tcss("tactical", str(out_path))
    content = out_path.read_text()
    assert "tactical" in content
