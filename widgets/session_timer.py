import time
from textual.widgets import Static
from widgets.base import CC4UWidget


class SessionTimerWidget(CC4UWidget):
    WIDGET_TYPE = "session_timer"
    WIDGET_TITLE = "SESSION TIMER"
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._start = time.time()

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        elapsed = int(time.time() - self._start)
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"[bold]{hours:02d}:{minutes:02d}:{seconds:02d}[/bold]"
