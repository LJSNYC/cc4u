import psutil
from textual.widgets import Static
from widgets.base import CC4UWidget


class NetworkWidget(CC4UWidget):
    WIDGET_TYPE = "network"
    WIDGET_TITLE = "NETWORK"
    REFRESH_RATE = 2.0
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        c = psutil.net_io_counters()
        self._prev_sent = c.bytes_sent
        self._prev_recv = c.bytes_recv

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        c = psutil.net_io_counters()
        sent = c.bytes_sent - self._prev_sent
        recv = c.bytes_recv - self._prev_recv
        self._prev_sent = c.bytes_sent
        self._prev_recv = c.bytes_recv

        def fmt(b: int) -> str:
            if b > 1_048_576:
                return f"{b / 1_048_576:.1f} MB/s"
            if b > 1024:
                return f"{b / 1024:.1f} KB/s"
            return f"{b} B/s"

        return f"[green]↓[/green] {fmt(recv)}\n[yellow]↑[/yellow] {fmt(sent)}"
