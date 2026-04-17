import os
from textual.widgets import Static
from textual.reactive import reactive

from widgets.base import CC4UWidget


class PomodoroWidget(CC4UWidget):
    WIDGET_TYPE = "pomodoro"
    WIDGET_TITLE = "POMODORO"

    WORK_SECONDS = 25 * 60
    BREAK_SECONDS = 5 * 60

    running: reactive[bool] = reactive(False)
    phase: reactive[str] = reactive("work")
    remaining: reactive[int] = reactive(25 * 60)
    sessions: reactive[int] = reactive(0)

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
        else:
            if self.phase == "work":
                self.sessions += 1
                self.phase = "break"
                self.remaining = self.BREAK_SECONDS
                os.system('osascript -e \'display notification "Break time!" with title "CC4U Pomodoro"\'')
            else:
                self.phase = "work"
                self.remaining = self.WORK_SECONDS
                os.system('osascript -e \'display notification "Back to work!" with title "CC4U Pomodoro"\'')
            # keep running across phase transitions

    def on_click(self) -> None:
        self.running = not self.running

    def watch_running(self, _) -> None:
        self._refresh_body()

    def watch_remaining(self, _) -> None:
        self._refresh_body()

    def _refresh_body(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        mins, secs = divmod(self.remaining, 60)
        total = self.WORK_SECONDS if self.phase == "work" else self.BREAK_SECONDS
        filled = int(10 * (total - self.remaining) / total)
        bar = "█" * filled + "░" * (10 - filled)

        phase_color = "green" if self.phase == "work" else "cyan"
        status = "▶" if self.running else "⏸"
        label = self.phase.upper()

        lines = [
            f"[{phase_color}]{label}[/{phase_color}]  {status}",
            f"[bold]{mins:02d}:{secs:02d}[/bold]",
            f"[dim]{bar}[/dim]",
            f"[dim]sessions: {self.sessions}[/dim]",
        ]
        return "\n".join(lines)
