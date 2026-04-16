import psutil
from textual.widgets import Static

from widgets.base import CC4UWidget


class CpuMemoryWidget(CC4UWidget):
    WIDGET_TYPE = "cpu_memory"
    WIDGET_TITLE = "SYS"
    REFRESH_RATE = 3.0

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._system_tick)

    def _system_tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def _bar(self, pct: float, width: int = 10) -> str:
        filled = int(width * pct / 100)
        filled = max(0, min(width, filled))
        color = "green" if pct < 60 else "yellow" if pct < 85 else "red"
        return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (width - filled)}[/dim]"

    def render_content(self) -> str:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        mem_used = mem.used / (1024 ** 3)
        mem_total = mem.total / (1024 ** 3)

        lines = [
            f"CPU  {self._bar(cpu)} {cpu:.0f}%",
            f"MEM  {self._bar(mem_pct)} {mem_used:.1f}/{mem_total:.0f}G",
        ]
        return "\n".join(lines)
