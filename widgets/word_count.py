from textual.widgets import Static
from widgets.base import CC4UWidget


class WordCountWidget(CC4UWidget):
    WIDGET_TYPE = "word_count"
    WIDGET_TITLE = "WORD COUNT"
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
            text = open(path).read()
            words = len(text.split())
            chars = len(text)
            lines = text.count("\n") + 1
            return (
                f"[bold]{words:,}[/bold] words\n"
                f"[dim]{chars:,} chars · {lines:,} lines[/dim]"
            )
        except FileNotFoundError:
            return f"[red]Not found[/red]\n[dim]{path}[/dim]"
