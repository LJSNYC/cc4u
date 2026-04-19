import json
import pytest


def test_poll_state_skips_render_when_data_unchanged(monkeypatch):
    """_poll_state must not call render_content when hash is identical."""
    import state as state_module
    from widgets.base import CC4UWidget

    render_calls = []

    class _TestWidget(CC4UWidget):
        WIDGET_TYPE = "test"
        STATE_KEYS: list = []

        def render_content(self) -> str:
            render_calls.append(1)
            return "content"

    monkeypatch.setattr(state_module, "_cache", {})
    monkeypatch.setattr(state_module, "_cache_ts", {})

    w = _TestWidget(cfg={})
    # Textual reactive fires watch_data synchronously when self.data is set,
    # even without a running app, so _poll_state() will trigger render_content.

    # Simulate first poll — should render (data hash is new)
    w._poll_state()
    assert len(render_calls) == 1, "render_content should be called on first poll"

    # Second poll with identical data — should NOT render (hash unchanged)
    w._poll_state()
    assert len(render_calls) == 1, "render_content should NOT be called when data is unchanged"


def test_poll_state_renders_when_data_changes(monkeypatch, tmp_path):
    """_poll_state must call render_content when data actually changed."""
    import state as state_module
    from widgets.base import CC4UWidget

    render_calls = []

    class _TestWidget(CC4UWidget):
        WIDGET_TYPE = "test"
        STATE_KEYS = ["session"]

        def render_content(self) -> str:
            render_calls.append(1)
            return "content"

    monkeypatch.setattr(state_module, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(state_module, "_cache", {})
    monkeypatch.setattr(state_module, "_cache_ts", {})
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 0.1}))

    w = _TestWidget(cfg={})
    w._poll_state()
    first_calls = len(render_calls)

    # Force cache expiry + change data
    monkeypatch.setattr(state_module, "_cache", {})
    monkeypatch.setattr(state_module, "_cache_ts", {})
    (tmp_path / "session.json").write_text(json.dumps({"cost_usd": 9.9}))

    w._poll_state()
    assert len(render_calls) > first_calls, "render_content should be called when data changes"
