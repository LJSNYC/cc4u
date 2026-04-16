import state as state_module
from textual.widgets import Static, Input
from widgets.base import CC4UWidget


class ChecklistWidget(CC4UWidget):
    WIDGET_TYPE = "checklist"
    WIDGET_TITLE = "CHECKLIST"
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._items: list = []
        self._adding: bool = False

    def on_mount(self) -> None:
        data = state_module.load_widget_data("checklist")
        self._items = data.get("items", [])

    def render_content(self) -> str:
        if not self._items:
            return "[dim]No items — click [bold]+[/bold] to add[/dim]"
        lines = []
        for item in self._items:
            mark = "[green]✓[/green]" if item.get("done") else "○"
            text = item.get("text", "")
            style = "[dim]" if item.get("done") else ""
            end = "[/dim]" if item.get("done") else ""
            lines.append(f"{mark} {style}{text}{end}")
        lines.append("[dim]+ add item[/dim]")
        return "\n".join(lines)

    def on_click(self, event) -> None:
        if self._adding:
            return
        add_row = 1 + len(self._items)  # title(1) + items
        if event.y >= add_row:
            self._start_add()
            return
        idx = event.y - 1
        if 0 <= idx < len(self._items):
            self._items[idx]["done"] = not self._items[idx].get("done", False)
            state_module.save_widget_data("checklist", {"items": self._items})
            self._refresh_body()

    def _start_add(self) -> None:
        self._adding = True
        inp = Input(placeholder="New item…", id="checklist-input")
        self.mount(inp)
        self.call_after_refresh(self._focus_input)

    def _focus_input(self) -> None:
        try:
            self.query_one("#checklist-input", Input).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._items.append({"text": text, "done": False})
            state_module.save_widget_data("checklist", {"items": self._items})
        self._stop_add()

    def on_key(self, event) -> None:
        if event.key == "escape" and self._adding:
            self._stop_add()

    def _stop_add(self) -> None:
        self._adding = False
        try:
            self.query_one("#checklist-input", Input).remove()
        except Exception:
            pass
        self._refresh_body()

    def _refresh_body(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass
