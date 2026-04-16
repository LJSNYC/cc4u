from datetime import datetime

from textual.widgets import Static

from widgets.base import CC4UWidget


class ClockWidget(CC4UWidget):
    WIDGET_TYPE = "clock"
    WIDGET_TITLE = "CLOCK"
    REFRESH_RATE = 1.0

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%a %b %d")
        return f"[bold]{time_str}[/bold]\n{date_str}"
