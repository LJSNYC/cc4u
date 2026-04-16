import json
import pytest
import state


def test_widget_data_path_returns_path_under_config(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    p = state.widget_data_path("checklist")
    assert str(p).endswith("checklist.json")


def test_load_widget_data_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    assert state.load_widget_data("checklist") == {}


def test_load_widget_data_returns_saved_data(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    (tmp_path / "checklist.json").write_text(json.dumps({"items": [{"text": "x", "done": False}]}))
    result = state.load_widget_data("checklist")
    assert result["items"][0]["text"] == "x"


def test_load_widget_data_tolerates_corrupt_json(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    (tmp_path / "checklist.json").write_text("NOT JSON {{")
    assert state.load_widget_data("checklist") == {}


def test_save_widget_data_writes_and_reads_back(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    state.save_widget_data("daily_goal", {"goal": "ship it"})
    assert state.load_widget_data("daily_goal")["goal"] == "ship it"


def test_save_widget_data_is_atomic(tmp_path, monkeypatch):
    """tmp file must not linger after save."""
    monkeypatch.setattr(state, "WIDGET_DATA_DIR", str(tmp_path))
    state.save_widget_data("x", {"v": 1})
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []
