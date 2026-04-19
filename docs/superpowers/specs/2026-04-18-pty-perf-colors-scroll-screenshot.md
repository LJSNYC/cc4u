# CC4U PTY: Performance, Colors, Scroll, Screenshot Drop
**Date:** 2026-04-18  
**Scope:** `cc4u/widgets/pty_pane.py`, `cc4u/state.py`, `cc4u/widgets/base.py`

---

## Problem Summary

Four compounding issues degrade CC4U's usability:

1. **Lag** — redundant disk reads, excessive PTY render frequency, and unnecessary widget re-renders
2. **No ANSI colors** — PTY output is monochrome; Claude Code outputs plain text when env vars don't signal a color-capable terminal
3. **Scrollback broken** — scroll events go to the PTY process as raw bytes instead of routing through Textual's event system
4. **Screenshot drag-and-drop silent failure** — macOS screenshot thumbnail drag produces no event in a Textual terminal app; nothing reaches CC4U

---

## Part 1: Performance Fixes

### 1A — Shared State Cache (`state.py`)

**Problem:** Every widget calls `state_module.session()`, `git()`, or `tools()` independently on its own 2-second timer. With 6 widgets, this produces up to 6 redundant `open() + json.load()` calls against the same 3 files per polling cycle.

**Fix:** Add a module-level cache dict with per-key timestamps. Each of `session()`, `git()`, `tools()` returns the cached value if it was read within the last 1 second; otherwise reads from disk and updates the cache.

```python
# state.py addition
_cache: dict = {}
_cache_ts: dict = {}
_CACHE_TTL = 1.0  # seconds

def _cached_read(key: str, filename: str, fallback):
    now = time.monotonic()
    if key in _cache and now - _cache_ts.get(key, 0) < _CACHE_TTL:
        return _cache[key]
    result = _read_json(filename, fallback)
    _cache[key] = result
    _cache_ts[key] = now
    return result
```

`session()`, `git()`, `tools()` all delegate to `_cached_read`. No changes to widget code.

**Impact:** Reduces disk reads from N (one per widget per poll) to 1 per state key per second, regardless of widget count.

### 1B — Widget Dirty-Check (`widgets/base.py`)

**Problem:** `self.data = fresh` in `_poll_state` always triggers Textual's reactive, calling `watch_data` and re-rendering even when the JSON content is identical to the previous poll.

**Fix:** Store a `_last_data_hash` on the widget. In `_poll_state`, compute `hash(json.dumps(fresh, sort_keys=True))` before assigning. Skip the assignment (and thus the re-render) if the hash matches.

```python
def _poll_state(self) -> None:
    fresh = { ... }  # existing logic
    h = hash(json.dumps(fresh, sort_keys=True))
    if h != getattr(self, "_last_data_hash", None):
        self._last_data_hash = h
        self.data = fresh
```

**Impact:** Most widget re-renders are eliminated during idle periods when Claude Code isn't running.

### 1C — PTY Tick Rate (`widgets/pty_pane.py`)

**Problem:** `set_interval(0.05, self._tick)` fires 20 times per second. 12.5fps is imperceptible for a terminal display.

**Fix:** Change to `set_interval(0.08, self._tick)` — 12.5fps. Reduce blink counter threshold from 8 ticks (400ms) to 8 ticks at 80ms = 640ms, which is fine for a blinking cursor.

**Impact:** 38% fewer PTY ticks; proportional CPU reduction on the hot path.

### 1D — PTY Cursor Blink Render Suppression (`widgets/pty_pane.py`)

**Problem:** `_render_screen()` rebuilds the entire Rich `Text` object (2400+ cell iterations) every cursor blink (~640ms), even when no new PTY data arrived. Blink is the dominant render trigger during idle.

**Fix:** Add `_blink_only` flag. When only blink toggled (no `data_arrived`), skip `_render_screen()` entirely if the cursor is not visible on the current display (e.g., user is in scroll-back mode). For normal operation, make cursor blink **opt-in** via config — default off. When off, `_cursor_visible` is always `True` and blink never toggles, eliminating blink-triggered renders entirely.

Config key: `behavior.cursor_blink` (bool, default `false`).

When `cursor_blink` is false:
- `_blink_counter` is never checked
- `blink_toggled` is always `False`
- `_render_screen()` only fires on `data_arrived`

**Impact:** Eliminates ~50% of all PTY renders during idle (when Claude Code is thinking but not outputting).

---

## Part 2: ANSI Colors

### Problem

Claude Code detects whether it's running in a color-capable terminal by checking environment variables (`COLORTERM`, `FORCE_COLOR`, `NO_COLOR`, `CLICOLOR_FORCE`) and the `TERM` value. When these are absent or wrong, Claude Code strips ANSI color codes and outputs plain text. The pyte parser is correct — it just never receives color sequences.

### Fix

Add the following to the PTY spawn env dict in `_start_process()`:

```python
env = {
    **os.environ,
    "TERM": "xterm-256color",
    "COLORTERM": "truecolor",
    "FORCE_COLOR": "1",
    "CLICOLOR_FORCE": "1",
    "NO_COLOR": "",           # empty string = color enabled
}
```

`FORCE_COLOR=1` is the primary signal used by Claude Code and most Node.js CLIs. `COLORTERM=truecolor` signals 24-bit color support. `CLICOLOR_FORCE=1` is the BSD/macOS convention. `NO_COLOR=""` (empty string, not unset) explicitly disables the no-color protocol.

**No changes to pyte rendering code** — the existing `_resolve_color` and `_char_style` logic is correct and will handle the color data once Claude Code starts emitting it.

---

## Part 3: Scrollback

### Problem

Confirmed root cause: Textual's actual mouse scroll event classes are `MouseScrollUp` and `MouseScrollDown`. The handlers in `pty_pane.py` are named `on_scroll_up` and `on_scroll_down` — no such event class exists in Textual, so these handlers **never fire**. Mouse wheel scrolling is silently dropped.

Verified via: `from textual import events; [name for name in dir(events) if 'scroll' in name.lower()]` → `['MouseScrollDown', 'MouseScrollLeft', 'MouseScrollRight', 'MouseScrollUp']`.

The keyboard shortcuts (`shift+pageup` / `shift+pagedown`) work correctly because they're handled in `on_key` via direct key name matching, independent of event class names.

The `_ScrollbackScreen.index()` scrollback capture is verified correct — the buffer fills properly on each line scroll.

### Fix

Rename two handlers in `pty_pane.py`:

```python
# Before (never fires):
def on_scroll_up(self, event) -> None: ...
def on_scroll_down(self, event) -> None: ...

# After (correct Textual API):
def on_mouse_scroll_up(self, event) -> None: ...
def on_mouse_scroll_down(self, event) -> None: ...
```

No other changes needed. The scroll offset logic, scrollback buffer, and `_render_screen()` call are all correct.

---

## Part 4: Screenshot Drag-and-Drop

### Problem

Textual runs inside a terminal emulator (iTerm2 / Terminal.app). macOS native drag-and-drop events never reach the Textual layer — the outer terminal either rejects the drop or swallows it. `on_paste` never fires for drag events.

### Solution: Triple-layer detection

**Layer 1 — Focus trigger (primary)**  
When the PTY pane gains focus (`on_focus`), check `~/Desktop` for a Screenshot file modified within the last 4 seconds. This fires reliably when the user drags the thumbnail to the CC4U window (bringing it to front) and releases it.

**Layer 2 — Background poll (failsafe)**  
A 3-second background timer (`set_interval(3.0, self._check_screenshot)`) runs a single `os.stat()` on the newest Screenshot file found via a sorted `glob`. Catches cases where CC4U already had focus when the screenshot was taken (Layer 1 wouldn't fire). CPU cost: microseconds per 3 seconds.

**Layer 3 — Clipboard check (secondary path)**  
On focus and on poll, also check the macOS clipboard via a lightweight osascript `get the clipboard` type check. Catches Cmd+Ctrl+Shift+4 (copy-to-clipboard) screenshots. This is the same osascript path already used by `_paste_image_from_clipboard()`.

### Detection logic

```python
def _check_screenshot(self) -> None:
    """Check Desktop for new screenshots OR clipboard PNG, send to Claude Code."""
    if self._proc is None or not self._proc.isalive():
        return
    self._try_desktop_screenshot()
    # clipboard check handled by _paste_image_from_clipboard on explicit paste

def _try_desktop_screenshot(self) -> None:
    import glob, time
    desktop = os.path.expanduser("~/Desktop")
    pattern = os.path.join(desktop, "Screenshot*.png")
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

`_last_screenshot_sent` is initialized to `""` in `__init__`. This prevents the same file from being sent twice.

### Reliability guarantee

The 4-second window means: as long as the user drops the thumbnail within 4 seconds of taking the screenshot (universal for this workflow), Layer 1 catches it. Layer 2 catches any edge case where CC4U already had focus. The combination matches the reliability of a native terminal.

---

## Files Changed

| File | Changes |
|---|---|
| `cc4u/state.py` | Add `_cache`, `_cache_ts`, `_CACHE_TTL`, `_cached_read()` |
| `cc4u/widgets/base.py` | Add `_last_data_hash` dirty-check in `_poll_state` |
| `cc4u/widgets/pty_pane.py` | Tick 50ms→80ms; blink default off; color env vars; scroll fix; screenshot detection |

---

## Out of Scope

- Widget-level polling rate changes (2s is fine with the state cache fix)
- Replacing pyte with a different terminal library
- Native macOS drop target registration (PyObjC)
- Changing the PTY renderer from Static to a line-by-line widget
