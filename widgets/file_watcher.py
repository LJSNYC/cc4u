import os
from datetime import datetime
from textual.widgets import Static
from widgets.base import CC4UWidget


class FileWatcherWidget(CC4UWidget):
    WIDGET_TYPE = "file_watcher"
    WIDGET_TITLE = "FILE WATCHER"
    REFRESH_RATE = 2.0
    STATE_KEYS = []

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        path = self.cfg.get("watch_path", "")
        if not path:
            return "[dim]No watch_path configured[/dim]"
        try:
            stat = os.stat(path)
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
            size = stat.st_size
            name = os.path.basename(path)
            if size > 1_048_576:
                size_str = f"{size / 1_048_576:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            return f"[bold]{name}[/bold]\n{size_str} · modified {mtime}"
        except FileNotFoundError:
            return f"[red]Not found[/red]\n[dim]{path}[/dim]"
