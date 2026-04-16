import json
import pytest
import state


def test_read_session_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    result = state.session()
    assert result == {}


def test_read_session_returns_data_when_file_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 0.042}))
    result = state.session()
    assert result["cost_usd"] == pytest.approx(0.042)


def test_read_git_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    assert state.git() == {}


def test_read_tools_returns_empty_list_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    assert state.tools() == []


def test_read_tolerates_corrupt_json(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    (tmp_path / "session.json").write_text("NOT JSON {{")
    assert state.session() == {}
