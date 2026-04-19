from __future__ import annotations

import glob
import os
import select
import shutil
import subprocess
import time
import uuid
from collections import deque

import pyte
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.events import Paste
from textual.widgets import Static

from widgets.base import CC4UWidget

_SCREENSHOT_DIR = os.path.expanduser("~/Desktop")

# ── ANSI color name → palette index ─────────────────────────────────────────
_PYTE_NAMED: dict[str, int] = {
    "black": 0, "red": 1, "green": 2, "brown": 3,
    "blue": 4, "magenta": 5, "cyan": 6, "white": 7,
    "brightblack": 8, "brightred": 9, "brightgreen": 10, "brightyellow": 11,
    "brightblue": 12, "brightmagenta": 13, "brightcyan": 14, "brightwhite": 15,
}

# 256-color lookup table — indices 0-15 are filled from theme palette at runtime
def _build_256_table() -> list[str]:
    t: list[str] = [""] * 16
    for r in range(6):
        for g in range(6):
            for b in range(6):
                rv = 0 if r == 0 else 55 + r * 40
                gv = 0 if g == 0 else 55 + g * 40
                bv = 0 if b == 0 else 55 + b * 40
                t.append(f"#{rv:02x}{gv:02x}{bv:02x}")
    for i in range(24):
        v = 8 + i * 10
        t.append(f"#{v:02x}{v:02x}{v:02x}")
    return t

_256_BASE = _build_256_table()

# Keys forwarded verbatim to the PTY as byte sequences
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


class _ScrollbackScreen(pyte.Screen):
    """pyte Screen subclass that captures lines as they scroll off the top."""

    def __init__(self, cols: int, rows: int, history: deque) -> None:
        super().__init__(cols, rows)
        self._history = history

    def index(self) -> None:
        # Snapshot the top line of the scroll region before it's discarded
        try:
            top = self.margins.top if self.margins else 0
            if top == 0:
                row = self.buffer[0]
                self._history.append(
                    {x: row.get(x) for x in range(self.columns)}
                )
        except Exception:
            pass
        super().index()


class PtyPane(CC4UWidget):
    """
    Live terminal pane — a drop-in replacement for running Claude Code in a
    real terminal.  Features: full ANSI color, blinking cursor, scrollback
    (mouse wheel or Shift+PgUp/Dn), text paste, image paste from macOS
    clipboard, and theme-aware terminal color palettes.
    """

    WIDGET_TYPE = "pty_pane"
    WIDGET_TITLE = "TERMINAL"
    STATE_KEYS: list[str] = []
    can_focus = True

    def __init__(self, cfg: dict, **kwargs) -> None:
        super().__init__(cfg, **kwargs)
        self._proc = None
        self._screen: _ScrollbackScreen | None = None
        self._stream: pyte.ByteStream | None = None
        raw_cmd = cfg.get("pty_command", "claude")
        self._cmd = shutil.which(raw_cmd) or raw_cmd
        self._scrollback: deque = deque(maxlen=2000)
        self._scroll_offset: int = 0
        self._palette: list[str] = self._default_palette()
        self._current_theme: str = ""
        self._cursor_visible: bool = True
        self._blink_counter: int = 0
        self._last_screenshot_sent: str = ""

    # ── Color palettes ───────────────────────────────────────────────────────

    @staticmethod
    def _default_palette() -> list[str]:
        """Fallback palette — yellow / light-blue / green to match widget themes."""
        return [
            "#1a1a1a", "#ff5555", "#50fa7b", "#f1fa8c",
            "#8be9fd", "#ff79c6", "#8be9fd", "#f8f8f2",
            "#555555", "#ff6e6e", "#69ff94", "#ffffa5",
            "#a4ffff", "#ff92df", "#a4ffff", "#ffffff",
        ]

    @staticmethod
    def _build_palette(colors: dict) -> list[str]:
        """Derive a 16-color ANSI palette from a theme's color dict."""
        bg      = colors.get("bg_primary",      "#1a1a1a")
        text    = colors.get("text_primary",     "#f8f8f2")
        muted   = colors.get("text_muted",       "#555555")
        danger  = colors.get("accent_danger",    "#ff5555")
        success = colors.get("accent_secondary", "#50fa7b")
        warn    = colors.get("accent_warn",      "#f1fa8c")
        info    = colors.get("accent_info",      "#8be9fd")
        primary = colors.get("accent_primary",   "#ff79c6")
        return [
            bg,      danger,  success, warn,
            info,    primary, info,    text,
            muted,   danger,  success, warn,
            info,    primary, info,    text,
        ]

    def _load_palette(self) -> None:
        try:
            from themes import load_theme
            colors = load_theme(self.app.theme).get("colors", {})
            self._palette = self._build_palette(colors)
        except Exception:
            self._palette = self._default_palette()

    # ── Compose / mount ──────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static(self.WIDGET_TITLE, id="widget-title", classes="widget-title")
        yield Static("", id="pty-output")

    def on_mount(self) -> None:
        self._load_palette()
        self._current_theme = getattr(self.app, "theme", "")
        self.call_after_refresh(self._start_process)
        self.set_interval(0.08, self._tick)          # was 0.05
        self.set_interval(3.0, self._check_screenshot)
        self.call_after_refresh(self.focus)

    # ── PTY lifecycle ────────────────────────────────────────────────────────

    def _init_pyte(self) -> None:
        rows = max(2, self.size.height - 2)
        cols = max(10, self.size.width - 2)
        self._screen = _ScrollbackScreen(cols, rows, self._scrollback)
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
                env={
                    **os.environ,
                    "TERM":           "xterm-256color",
                    "COLORTERM":      "truecolor",
                    "FORCE_COLOR":    "1",
                    "CLICOLOR_FORCE": "1",
                    "NO_COLOR":       "",
                },
            )
        except Exception as exc:
            try:
                self.query_one("#pty-output", Static).update(
                    f"Failed to start '{self._cmd}': {exc}"
                )
            except Exception:
                pass

    # ── Main tick ────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        # Reload palette if the app theme was changed
        current = getattr(self.app, "theme", "")
        if current != self._current_theme:
            self._current_theme = current
            self._load_palette()

        if self._proc is None or not self._proc.isalive():
            try:
                self.query_one("#pty-output", Static).update(
                    "[dim]Process ended — click to restart[/dim]"
                )
            except Exception:
                pass
            return

        data_arrived = False
        try:
            while True:
                ready, _, _ = select.select([self._proc.fd], [], [], 0)
                if not ready:
                    break
                data = self._proc.read(65536)
                if data and self._stream is not None:
                    self._stream.feed(data)
                    data_arrived = True
        except Exception:
            pass

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

    # ── Color helpers ────────────────────────────────────────────────────────

    def _resolve_color(self, val) -> str | None:
        """Convert a pyte color value to a Rich-compatible hex string."""
        if val is None or val == "default":
            return None
        if isinstance(val, str):
            if val in _PYTE_NAMED:
                return self._palette[_PYTE_NAMED[val]]
            if val.startswith("#") and len(val) == 7:
                return val
            # pyte encodes 256-color as "color{N}"
            if val.startswith("color") and val[5:].isdigit():
                n = int(val[5:])
                if n < 16:
                    return self._palette[n]
                return _256_BASE[n] if n < 256 else None
        if isinstance(val, int):
            if val < 16:
                return self._palette[val]
            return _256_BASE[val] if val < 256 else None
        return None

    def _char_style(self, char, is_cursor: bool = False) -> Style:
        if char is None:
            return Style()
        try:
            fg_raw = char.fg
            bg_raw = char.bg
            bold   = getattr(char, "bold",         False)
            italic = getattr(char, "italics",       False)
            under  = getattr(char, "underscore",    False)
            strike = getattr(char, "strikethrough", False)
            rev    = getattr(char, "reverse",       False)
        except AttributeError:
            return Style()

        if is_cursor:
            # Inverted block cursor: swap fg and bg, ensure both are visible
            fg = self._resolve_color(bg_raw) or self._palette[0]
            bg = self._resolve_color(fg_raw) or self._palette[7]
            return Style(color=fg, bgcolor=bg, bold=True)

        if rev:
            fg_raw, bg_raw = bg_raw, fg_raw

        return Style(
            color=self._resolve_color(fg_raw),
            bgcolor=self._resolve_color(bg_raw),
            bold=bold,
            italic=italic,
            underline=under,
            strike=strike,
        )

    # ── Rendering ────────────────────────────────────────────────────────────

    def _render_row(self, row: dict, is_cursor_row: bool, cursor_x: int) -> Text:
        line = Text()
        cols = self._screen.columns if self._screen else 80
        for x in range(cols):
            char = row.get(x) if row is not None else None
            ch = (char.data if char and char.data else " ")
            is_cur = is_cursor_row and x == cursor_x and self._cursor_visible
            line.append(ch, style=self._char_style(char, is_cursor=is_cur))
        return line

    def _render_screen(self) -> None:
        if self._screen is None:
            return

        visible = self._screen.lines
        cursor_x = self._screen.cursor.x
        cursor_y = self._screen.cursor.y

        if self._scroll_offset > 0:
            sb = list(self._scrollback)
            current = [self._screen.buffer[y] for y in range(visible)]
            all_rows = sb + current
            total = len(all_rows)
            end = max(0, total - self._scroll_offset)
            start = max(0, end - visible)
            display_rows = all_rows[start:end]
            in_scroll = True
        else:
            display_rows = [self._screen.buffer[y] for y in range(visible)]
            in_scroll = False

        lines: list[Text] = []
        for i, row in enumerate(display_rows):
            is_cur_row = (not in_scroll) and (i == cursor_y)
            lines.append(self._render_row(row, is_cur_row, cursor_x))

        # Pad to fill widget height
        while len(lines) < visible:
            lines.append(self._render_row({}, False, 0))

        # Scroll indicator on last line when in scroll mode
        if in_scroll:
            lines[-1] = Text(
                f" \u2191 scrolled back {self._scroll_offset} lines"
                "  \u2014  Shift+\u2193 / scroll down to return ",
                style=Style(color="#000000", bgcolor="#888888"),
            )

        output = Text()
        for i, line in enumerate(lines):
            if i > 0:
                output.append("\n")
            output.append_text(line)

        try:
            self.query_one("#pty-output", Static).update(output)
        except Exception:
            pass

    # ── Paste handling ───────────────────────────────────────────────────────

    def on_paste(self, event: Paste) -> None:
        """Forward text paste to the PTY (handles Cmd+V and file drag-drop paths)."""
        if self._proc is None or not self._proc.isalive():
            return
        if event.text:
            try:
                self._proc.write(event.text.encode("utf-8"))
                event.stop()
            except Exception:
                pass
        else:
            # No text — clipboard may hold image data
            if self._paste_image_from_clipboard():
                event.stop()

    def _paste_image_from_clipboard(self) -> bool:
        """
        macOS only: save clipboard PNG to /tmp and type its path into the PTY.
        Handles screenshots dragged from the macOS thumbnail (bottom-right corner)
        or copied via Cmd+Shift+4 / Cmd+Ctrl+Shift+3.
        """
        tmp_path = f"/tmp/cc4u_img_{uuid.uuid4().hex[:8]}.png"
        script = (
            "try\n"
            f"    set d to the clipboard as \u00abclass PNGf\u00bb\n"
            f'    set f to open for access POSIX file "{tmp_path}" with write permission\n'
            "    set eof of f to 0\n"
            "    write d to f\n"
            "    close access f\n"
            f'    return "{tmp_path}"\n'
            "on error\n"
            '    return ""\n'
            "end try"
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5,
            )
            path = result.stdout.strip()
            if path and os.path.exists(path) and os.path.getsize(path) > 0:
                self._proc.write(path.encode("utf-8"))
                return True
        except Exception:
            pass
        return False

    # ── Key input ────────────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        if self._proc is None or not self._proc.isalive():
            return
        if not self.has_focus:
            return

        # Scrollback navigation — never forwarded to the PTY
        if event.key == "shift+pageup":
            if self._screen:
                self._scroll_offset = min(
                    self._scroll_offset + self._screen.lines,
                    len(self._scrollback),
                )
                self._render_screen()
            event.stop()
            return
        if event.key in ("shift+pagedown", "shift+end"):
            self._scroll_offset = max(0, self._scroll_offset - (
                self._screen.lines if self._screen else 20
            ))
            self._render_screen()
            event.stop()
            return

        # Any other keystroke exits scroll mode before forwarding
        if self._scroll_offset > 0:
            self._scroll_offset = 0

        seq = _KEY_BYTES.get(event.key)
        if seq is not None:
            try:
                self._proc.write(seq)
                event.stop()
            except Exception:
                pass
            return

        char = event.character
        if char:
            try:
                self._proc.write(char.encode("utf-8"))
                event.stop()
            except Exception:
                pass

    def on_mouse_scroll_up(self, event) -> None:
        self._scroll_offset = min(
            self._scroll_offset + 3, len(self._scrollback)
        )
        self._render_screen()
        event.stop()

    def on_mouse_scroll_down(self, event) -> None:
        self._scroll_offset = max(0, self._scroll_offset - 3)
        self._render_screen()
        event.stop()

    def on_focus(self, event=None) -> None:
        self._check_screenshot()

    def _check_screenshot(self) -> None:
        if self._proc is None or not self._proc.isalive():
            return
        self._try_desktop_screenshot()

    def _try_desktop_screenshot(self) -> None:
        pattern = os.path.join(_SCREENSHOT_DIR, "Screenshot*.png")
        files = glob.glob(pattern)
        if not files:
            return
        newest = max(files, key=os.path.getmtime)
        mtime = os.path.getmtime(newest)
        age = time.time() - mtime
        if age < 4.0 and newest != self._last_screenshot_sent:
            self._last_screenshot_sent = newest
            try:
                self._proc.write(newest.encode("utf-8"))
            except Exception:
                pass

    def on_click(self, event) -> None:
        if self._proc is None or not self._proc.isalive():
            self._scrollback.clear()
            self._scroll_offset = 0
            self.call_after_refresh(self._start_process)
        self.focus()

    # ── Resize ───────────────────────────────────────────────────────────────

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

    # ── Cleanup ──────────────────────────────────────────────────────────────

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
