import time
from textual.widgets import Static
from widgets.base import CC4UWidget


class UptimeWidget(CC4UWidget):
    WIDGET_TYPE = "uptime"
    WIDGET_TITLE = "UPTIME"
    REFRESH_RATE = 10.0
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._start = time.time()

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        elapsed = int(time.time() - self._start)
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        days = hours // 24
        hours = hours % 24
        if days > 0:
            return f"[bold]{days}d {hours:02d}h {minutes:02d}m[/bold]"
        return f"[bold]{hours:02d}:{minutes:02d}:{seconds:02d}[/bold]"
