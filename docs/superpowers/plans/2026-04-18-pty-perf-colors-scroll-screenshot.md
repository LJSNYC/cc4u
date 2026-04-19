# PTY Performance, Colors, Scroll & Screenshot Drop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix four compounding PTY issues: redundant disk I/O causing lag, missing ANSI color env vars making Claude Code render plain text, wrong Textual event handler names breaking mouse scroll, and no macOS screenshot drag-and-drop support.

**Architecture:** All changes are surgical edits to three files — `state.py` gets a module-level 1-second TTL cache; `widgets/base.py` gets a hash-based dirty-check before re-rendering; `widgets/pty_pane.py` gets corrected event handler names, ANSI-forcing env vars, reduced tick/blink rates, and a focus-triggered + polled screenshot detector.

**Tech Stack:** Python 3, Textual 8.x, pyte, ptyprocess, glob/os/time (stdlib)

---

## File Map

| File | What changes |
|---|---|
| `cc4u/state.py` | Add `_cache`, `_cache_ts`, `_CACHE_TTL`, `_cached_read()` |
| `cc4u/widgets/base.py` | Add `import json`, `_last_data_hash` dirty-check in `_poll_state` |
| `cc4u/widgets/pty_pane.py` | Tick 50ms→80ms; blink default off; color env vars; rename scroll handlers; screenshot detection |
| `cc4u/tests/test_state.py` | Add cache hit/miss/expiry tests |
| `cc4u/tests/test_widgets_base.py` | New file — dirty-check tests |
| `cc4u/tests/test_pty_pane.py` | New file — env vars, screenshot detection, scroll handler existence |

---

## Task 1: State Cache

**Files:**
- Modify: `cc4u/state.py`
- Modify: `cc4u/tests/test_state.py`

- [ ] **Step 1: Write failing tests for cache behavior**

Add to `cc4u/tests/test_state.py`:

```python
import time as _time

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/cc4u && python3 -m pytest tests/test_state.py::test_session_returns_cached_value_within_ttl tests/test_state.py::test_session_refreshes_after_ttl_expires -v
```

Expected: `AttributeError: module 'state' has no attribute '_cache'`

- [ ] **Step 3: Implement the cache in `state.py`**

Replace the entire file with:

```python
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
```

- [ ] **Step 4: Run all state tests**

```bash
cd ~/cc4u && python3 -m pytest tests/test_state.py -v
```

Expected: All pass.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
cd ~/cc4u && python3 -m pytest tests/ -q
```

Expected: 100 passed (same as before).

- [ ] **Step 6: Commit**

```bash
cd ~/cc4u && git add cc4u/state.py tests/test_state.py && git commit -m "perf: add 1s TTL cache to state reads — eliminates redundant disk I/O"
```

---

## Task 2: Widget Dirty-Check

**Files:**
- Modify: `cc4u/widgets/base.py`
- Create: `cc4u/tests/test_widgets_base.py`

- [ ] **Step 1: Write failing test**

Create `cc4u/tests/test_widgets_base.py`:

```python
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
    # Simulate first poll — should render
    w._poll_state()
    assert len(render_calls) == 1

    # Second poll with identical data — should NOT render
    w._poll_state()
    assert len(render_calls) == 1


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
    assert len(render_calls) > first_calls
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/cc4u && python3 -m pytest tests/test_widgets_base.py -v
```

Expected: `AttributeError: 'CC4UWidget' object has no attribute '_last_data_hash'` or the render-skip assertion fails.

- [ ] **Step 3: Add dirty-check to `widgets/base.py`**

Add `import json` to the imports at the top of `cc4u/widgets/base.py`:

```python
import json

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

import state as state_module
```

Replace `_poll_state` in `cc4u/widgets/base.py`:

```python
def _poll_state(self) -> None:
    fresh = {}
    if "session" in self.STATE_KEYS:
        fresh["session"] = state_module.session()
    if "git" in self.STATE_KEYS:
        fresh["git"] = state_module.git()
    if "tools" in self.STATE_KEYS:
        fresh["tools"] = state_module.tools()
    h = hash(json.dumps(fresh, sort_keys=True))
    if h != getattr(self, "_last_data_hash", None):
        self._last_data_hash = h
        self.data = fresh
```

- [ ] **Step 4: Run dirty-check tests**

```bash
cd ~/cc4u && python3 -m pytest tests/test_widgets_base.py -v
```

Expected: Both pass.

- [ ] **Step 5: Run full suite**

```bash
cd ~/cc4u && python3 -m pytest tests/ -q
```

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
cd ~/cc4u && git add cc4u/widgets/base.py tests/test_widgets_base.py && git commit -m "perf: skip widget re-render when polled data is unchanged"
```

---

## Task 3: PTY Fixes (Tick, Blink, Colors, Scroll)

**Files:**
- Modify: `cc4u/widgets/pty_pane.py`
- Create: `cc4u/tests/test_pty_pane.py`

- [ ] **Step 1: Write failing tests**

Create `cc4u/tests/test_pty_pane.py`:

```python
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

    # Replace classmethod on the class — monkeypatch handles descriptor removal
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

    # Create a fake screenshot file modified "now"
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
    # Backdate the file mtime by 10 seconds
    old_time = time.time() - 10
    os.utime(str(screenshot), (old_time, old_time))
    monkeypatch.setattr("widgets.pty_pane._SCREENSHOT_DIR", str(tmp_path))

    pane._try_desktop_screenshot()

    assert written == [], "Old screenshot should not be sent"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/cc4u && python3 -m pytest tests/test_pty_pane.py -v
```

Expected: All 5 fail — env vars missing, old handler names present, `_SCREENSHOT_DIR` not defined, etc.

- [ ] **Step 3: Apply all four PTY fixes to `pty_pane.py`**

**3a — Module-level constant for screenshot dir** (add near top of file, after imports):

```python
_SCREENSHOT_DIR = os.path.expanduser("~/Desktop")
```

**3b — `__init__`: add `_last_screenshot_sent`**

In `PtyPane.__init__`, after `self._blink_counter: int = 0`, add:

```python
self._last_screenshot_sent: str = ""
```

**3c — `on_mount`: slow tick, add screenshot poll**

Replace the `set_interval` call in `on_mount`:

```python
def on_mount(self) -> None:
    self._load_palette()
    self._current_theme = getattr(self.app, "theme", "")
    self.call_after_refresh(self._start_process)
    self.set_interval(0.08, self._tick)          # was 0.05
    self.set_interval(3.0, self._check_screenshot)
    self.call_after_refresh(self.focus)
```

**3d — `_start_process`: color-forcing env vars**

Replace the `env=` argument in `_start_process`:

```python
self._proc = ptyprocess.PtyProcess.spawn(
    [self._cmd],
    dimensions=(rows, cols),
    env={
        **os.environ,
        "TERM":          "xterm-256color",
        "COLORTERM":     "truecolor",
        "FORCE_COLOR":   "1",
        "CLICOLOR_FORCE": "1",
        "NO_COLOR":      "",
    },
)
```

**3e — `_tick`: disable cursor blink by default**

Replace the blink section inside `_tick` (the block after `data_arrived = False`):

```python
# Cursor blink — only when explicitly enabled in config
blink_toggled = False
cursor_blink = self.cfg.get("cursor_blink", False)
if cursor_blink:
    self._blink_counter += 1
    if self._blink_counter >= 8:
        self._cursor_visible = not self._cursor_visible
        self._blink_counter = 0
        blink_toggled = True

if data_arrived or blink_toggled:
    self._render_screen()
    if self._screen and self._screen.dirty:
        self._screen.dirty.clear()
```

**3f — Rename scroll handlers**

Replace:
```python
def on_scroll_up(self, event) -> None:
```
with:
```python
def on_mouse_scroll_up(self, event) -> None:
```

Replace:
```python
def on_scroll_down(self, event) -> None:
```
with:
```python
def on_mouse_scroll_down(self, event) -> None:
```

**3g — Add `import glob` to module-level imports and screenshot detection methods**

Add `import glob` to the import block at the top of `pty_pane.py` (alongside the existing `import os`, `import time`, etc.):

```python
import glob
```

Add these three methods after `on_mouse_scroll_down`:

```python
def on_focus(self, event=None) -> None:
    self._check_screenshot()

def _check_screenshot(self) -> None:
    if self._proc is None or not self._proc.isalive():
        return
    self._try_desktop_screenshot()

def _try_desktop_screenshot(self) -> None:
    pattern = os.path.join(_SCREENSHOT_DIR, "Screenshot*.png")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        return
    newest = files[0]
    age = time.time() - os.path.getmtime(newest)
    if age < 4.0 and newest != self._last_screenshot_sent:
        self._last_screenshot_sent = newest
        try:
            self._proc.write(newest.encode("utf-8"))
        except Exception:
            pass
```

- [ ] **Step 4: Run PTY tests**

```bash
cd ~/cc4u && python3 -m pytest tests/test_pty_pane.py -v
```

Expected: All 5 pass.

- [ ] **Step 5: Run full suite**

```bash
cd ~/cc4u && python3 -m pytest tests/ -q
```

Expected: All pass (new total will be 100 + new tests).

- [ ] **Step 6: Commit**

```bash
cd ~/cc4u && git add cc4u/widgets/pty_pane.py tests/test_pty_pane.py && git commit -m "fix: ANSI colors, mouse scroll, screenshot drop, tick perf in PtyPane"
```

---

## Task 4: Manual Verification

These behavioral changes can't be fully unit-tested — verify them live.

- [ ] **Step 1: Launch CC4U**

```bash
cd ~/cc4u && python3 -m cc4u
```

- [ ] **Step 2: Verify ANSI colors**

In the PTY, let Claude Code run any command that produces output (e.g., ask it to read a file). Confirm:
- Tool names (Read, Bash, Write) appear in **green**
- Bullet points (●) appear colored
- Different text categories (descriptions vs. code) are visually distinct
- Compare against a native Claude Code terminal if unsure

- [ ] **Step 3: Verify mouse scroll**

While Claude Code has produced several screens of output, scroll the mouse wheel **up** over the PTY pane. Confirm:
- Content scrolls back through history
- The "↑ scrolled back N lines" indicator appears on the last line
- Scrolling back down returns to live output

- [ ] **Step 4: Verify screenshot drag-and-drop**

1. Take a screenshot (Cmd+Shift+4, drag to capture an area)
2. The thumbnail appears bottom-right of screen
3. Drag the thumbnail to the CC4U window
4. Confirm the screenshot file path is typed into Claude Code within ~1 second of dropping

- [ ] **Step 5: Verify no new lag**

Run CC4U for 30 seconds while Claude Code is active. The app should feel at least as responsive as before — ideally less sluggish during idle (no blink renders). If any new lag is observed, check whether the 3s screenshot poll is the cause by temporarily removing `self.set_interval(3.0, self._check_screenshot)`.

- [ ] **Step 6: Ship**

```bash
cd ~/cc4u && git add cc4u/widgets/pty_pane.py cc4u/state.py cc4u/widgets/base.py && git push origin main
```

Or use the one-shot command (all changes are already committed by this point, so just push):

```bash
git push origin main
```
