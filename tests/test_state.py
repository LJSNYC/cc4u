import json
import pytest
import state


def test_read_session_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    result = state.session()
    assert result == {}


def test_read_session_returns_data_when_file_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 0.042}))
    result = state.session()
    assert result["cost_usd"] == pytest.approx(0.042)


def test_read_git_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    assert state.git() == {}


def test_read_tools_returns_empty_list_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    assert state.tools() == []


def test_read_tolerates_corrupt_json(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    (tmp_path / "session.json").write_text("NOT JSON {{")
    assert state.session() == {}


def test_session_returns_cached_value_within_ttl(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 0.5}))
    first = state.session()
    # Overwrite file — cache should still return stale value
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 9.9}))
    second = state.session()
    assert second["cost_usd"] == pytest.approx(0.5)


def test_session_refreshes_after_ttl_expires(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    # Set cache_ts to 0 so TTL is always expired
    monkeypatch.setattr(state, "_cache_ts", {"session": 0.0})
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 9.9}))
    result = state.session()
    assert result["cost_usd"] == pytest.approx(9.9)


def test_git_cached_independently_from_session(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    (tmp_path / "git.json").write_text(json.dumps({"branch": "main"}))
    result = state.git()
    assert result["branch"] == "main"


def test_tools_cached_independently(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state, "_cache", {})
    monkeypatch.setattr(state, "_cache_ts", {})
    (tmp_path / "tools.json").write_text(json.dumps([{"tool": "Read"}]))
    result = state.tools()
    assert result == [{"tool": "Read"}]
