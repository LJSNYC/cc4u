import os
from textual.widgets import Static
from widgets.base import CC4UWidget

_MAX_ENTRIES = 18


class DirTreeWidget(CC4UWidget):
    WIDGET_TYPE = "dir_tree"
    WIDGET_TITLE = "DIR TREE"
    REFRESH_RATE = 5.0
    STATE_KEYS = []

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._tick)

    def _tick(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        root = os.getcwd()
        lines = [f"[bold]{os.path.basename(root)}/[/bold]"]
        try:
            entries = sorted(os.listdir(root))[:_MAX_ENTRIES]
            for entry in entries:
                if entry.startswith("."):
                    continue
                full = os.path.join(root, entry)
                if os.path.isdir(full):
                    lines.append(f"  [blue]{entry}/[/blue]")
                else:
                    lines.append(f"  [dim]{entry}[/dim]")
        except PermissionError:
            lines.append("  [red]Permission denied[/red]")
        return "\n".join(lines)
