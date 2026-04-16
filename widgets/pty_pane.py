from __future__ import annotations

import os
import select
import shutil
import time

import pyte
from textual.app import ComposeResult
from textual.widgets import Static
from widgets.base import CC4UWidget


# Map Textual key names → byte sequences to send to the PTY
_KEY_BYTES: dict[str, bytes] = {
    "enter":      b"\r",
    "escape":     b"\x1b",
    "backspace":  b"\x7f",
    "delete":     b"\x1b[3~",
    "tab":        b"\t",
    "up":         b"\x1b[A",
    "down":       b"\x1b[B",
    "right":      b"\x1b[C",
    "left":       b"\x1b[D",
    "home":       b"\x1b[H",
    "end":        b"\x1b[F",
    "pageup":     b"\x1b[5~",
    "pagedown":   b"\x1b[6~",
    "ctrl+c":     b"\x03",
    "ctrl+d":     b"\x04",
    "ctrl+z":     b"\x1a",
    "ctrl+l":     b"\x0c",
    "ctrl+a":     b"\x01",
    "ctrl+e":     b"\x05",
    "ctrl+u":     b"\x15",
    "ctrl+k":     b"\x0b",
}


class PtyPane(CC4UWidget):
    """
    Live terminal pane. Spawns a subprocess (default: 'claude') in a PTY,
    runs output through a pyte VT100 screen buffer, and renders the current
    screen state into a Static widget every 50 ms.

    Uses select() before every read so _tick() never blocks the event loop.
    """

    WIDGET_TYPE = "pty_pane"
    WIDGET_TITLE = "TERMINAL"
    STATE_KEYS = []
    can_focus = True          # must be True to receive keyboard events

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._proc = None
        self._screen: pyte.Screen | None = None
        self._stream: pyte.ByteStream | None = None
        raw_cmd = cfg.get("pty_command", "claude")
        self._cmd = shutil.which(raw_cmd) or raw_cmd

    def compose(self) -> ComposeResult:
        yield Static(self.WIDGET_TITLE, id="widget-title", classes="widget-title")
        yield Static("", id="pty-output")

    def on_mount(self) -> None:
        self.call_after_refresh(self._start_process)
        self.set_interval(0.05, self._tick)
        # Grab focus so keyboard input reaches the PTY immediately
        self.call_after_refresh(self.focus)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _init_pyte(self) -> None:
        rows = max(2, self.size.height - 2)
        cols = max(10, self.size.width - 2)
        self._screen = pyte.Screen(cols, rows)
        self._stream = pyte.ByteStream(self._screen)

    def _start_process(self) -> None:
        self._init_pyte()
        rows = self._screen.lines
        cols = self._screen.columns
        try:
            import ptyprocess
            self._proc = ptyprocess.PtyProcess.spawn(
                [self._cmd],
                dimensions=(rows, cols),
                env={**os.environ, "TERM": "xterm-256color"},
            )
        except Exception as exc:
            try:
                self.query_one("#pty-output", Static).update(
                    f"Failed to start '{self._cmd}': {exc}"
                )
            except Exception:
                pass

    def _tick(self) -> None:
        """Non-blocking tick: drain PTY output then refresh the screen buffer."""
        if self._proc is None or not self._proc.isalive():
            return
        try:
            # select() with timeout=0 returns immediately — never blocks
            ready, _, _ = select.select([self._proc.fd], [], [], 0)
            if ready:
                data = self._proc.read(4096)
                if data and self._stream is not None:
                    self._stream.feed(data)
        except Exception:
            pass
        self._render_screen()

    def _render_screen(self) -> None:
        if self._screen is None:
            return
        lines = []
        for y in range(self._screen.lines):
            row = self._screen.buffer[y]
            line = "".join(
                (row[x].data or " ") for x in range(self._screen.columns)
            ).rstrip()
            lines.append(line)
        # Trim trailing blank lines
        while lines and not lines[-1]:
            lines.pop()
        try:
            self.query_one("#pty-output", Static).update("\n".join(lines))
        except Exception:
            pass

    # ── Input forwarding ────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        if self._proc is None or not self._proc.isalive():
            return
        if not self.has_focus:
            return
        # Check named key sequences first (enter, arrows, ctrl+x, etc.)
        seq = _KEY_BYTES.get(event.key)
        if seq is not None:
            try:
                self._proc.write(seq)
                event.stop()
            except Exception:
                pass
            return
        # Fall back to printable character
        char = event.character
        if char:
            try:
                self._proc.write(char.encode("utf-8"))
                event.stop()
            except Exception:
                pass

    def on_click(self, event) -> None:
        """Click on the pane to grab focus."""
        self.focus()

    # ── Resize ──────────────────────────────────────────────────────────────

    def on_resize(self, event) -> None:
        rows = max(2, event.size.height - 2)
        cols = max(10, event.size.width - 2)
        if self._screen is not None:
            self._screen.resize(rows, cols)
        if self._proc is not None and self._proc.isalive():
            try:
                self._proc.setwinsize(rows, cols)
            except Exception:
                pass

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def on_unmount(self) -> None:
        self._terminate()

    def _terminate(self) -> None:
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            deadline = time.time() + 2.0
            while self._proc.isalive() and time.time() < deadline:
                time.sleep(0.05)
            if self._proc.isalive():
                self._proc.terminate(force=True)
        except Exception:
            pass
        self._proc = None

    def render_content(self) -> str:
        return ""
