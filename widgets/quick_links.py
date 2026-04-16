import webbrowser
import state as state_module
from textual.widgets import Static
from widgets.base import CC4UWidget


class QuickLinksWidget(CC4UWidget):
    WIDGET_TYPE = "quick_links"

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._links: list = []
    WIDGET_TITLE = "QUICK LINKS"
    STATE_KEYS = []

    def on_mount(self) -> None:
        data = state_module.load_widget_data("quick_links")
        self._links = data.get("links", [])

    def on_click(self, event) -> None:
        idx = event.y - 1
        if 0 <= idx < len(self._links):
            url = self._links[idx].get("url", "")
            if url:
                webbrowser.open(url)

    def render_content(self) -> str:
        if not self._links:
            return "[dim]No links — add to quick_links.json[/dim]"
        lines = []
        for link in self._links:
            label = link.get("label", link.get("url", "?"))
            lines.append(f"[cyan]→[/cyan] {label}")
        return "\n".join(lines)
