import os
import pytest


def test_pty_spawn_env_includes_color_forcing_vars(monkeypatch):
    """PTY spawn env must include all four color-forcing vars."""
    import ptyprocess
    from widgets.pty_pane import PtyPane

    captured_env = [None]

    class _FakeProc:
        def isalive(self): return True

    def fake_spawn(cmd, dimensions, env):
        captured_env[0] = env
        return _FakeProc()

    monkeypatch.setattr(ptyprocess.PtyProcess, "spawn", fake_spawn)

    pane = PtyPane(cfg={})
    pane._init_pyte = lambda: None
    pane._screen = type("S", (), {"lines": 24, "columns": 80})()
    pane._start_process()

    env = captured_env[0]
    assert env is not None, "spawn was never called"
    assert env.get("COLORTERM") == "truecolor"
    assert env.get("FORCE_COLOR") == "1"
    assert env.get("CLICOLOR_FORCE") == "1"
    assert env.get("NO_COLOR") == ""
    assert env.get("TERM") == "xterm-256color"


def test_scroll_handlers_are_mouse_scroll_events():
    """on_mouse_scroll_up/down must exist; old on_scroll_up/down must not."""
    from widgets.pty_pane import PtyPane
    assert hasattr(PtyPane, "on_mouse_scroll_up"), \
        "on_mouse_scroll_up missing — mouse scroll will never fire"
    assert hasattr(PtyPane, "on_mouse_scroll_down"), \
        "on_mouse_scroll_down missing — mouse scroll will never fire"
    assert not hasattr(PtyPane, "on_scroll_up"), \
        "on_scroll_up still present — remove the old handler"
    assert not hasattr(PtyPane, "on_scroll_down"), \
        "on_scroll_down still present — remove the old handler"


def test_screenshot_detection_sends_new_file(tmp_path, monkeypatch):
    """_try_desktop_screenshot must write the path to PTY when file is fresh."""
    import time
    from widgets.pty_pane import PtyPane

    written = []

    class _FakeProc:
        def isalive(self): return True
        def write(self, data): written.append(data)

    pane = PtyPane(cfg={})
    pane._proc = _FakeProc()

    screenshot = tmp_path / "Screenshot 2026-04-18 at 20.00.00.png"
    screenshot.write_bytes(b"\x89PNG")
    monkeypatch.setattr("widgets.pty_pane._SCREENSHOT_DIR", str(tmp_path))

    pane._try_desktop_screenshot()

    assert written == [str(screenshot).encode("utf-8")]


def test_screenshot_not_sent_twice(tmp_path, monkeypatch):
    """Same screenshot file must not be sent a second time."""
    from widgets.pty_pane import PtyPane

    written = []

    class _FakeProc:
        def isalive(self): return True
        def write(self, data): written.append(data)

    pane = PtyPane(cfg={})
    pane._proc = _FakeProc()

    screenshot = tmp_path / "Screenshot 2026-04-18 at 20.00.00.png"
    screenshot.write_bytes(b"\x89PNG")
    monkeypatch.setattr("widgets.pty_pane._SCREENSHOT_DIR", str(tmp_path))

    pane._try_desktop_screenshot()
    pane._try_desktop_screenshot()

    assert len(written) == 1, "Screenshot was sent more than once"


def test_screenshot_not_sent_if_older_than_4s(tmp_path, monkeypatch):
    """Screenshot files older than 4 seconds must be ignored."""
    import time
    from widgets.pty_pane import PtyPane

    written = []

    class _FakeProc:
        def isalive(self): return True
        def write(self, data): written.append(data)

    pane = PtyPane(cfg={})
    pane._proc = _FakeProc()

    screenshot = tmp_path / "Screenshot 2026-04-18 at 19.00.00.png"
    screenshot.write_bytes(b"\x89PNG")
    old_time = time.time() - 10
    os.utime(str(screenshot), (old_time, old_time))
    monkeypatch.setattr("widgets.pty_pane._SCREENSHOT_DIR", str(tmp_path))

    pane._try_desktop_screenshot()

    assert written == [], "Old screenshot should not be sent"


def test_on_focus_triggers_screenshot_check(monkeypatch):
    from widgets.pty_pane import PtyPane
    checked = []
    pane = PtyPane(cfg={})
    monkeypatch.setattr(pane, "_check_screenshot", lambda: checked.append(1))
    pane.on_focus()
    assert checked == [1]
