import state as state_module
from textual.widgets import Static, TextArea
from widgets.base import CC4UWidget


class ProjectNotesWidget(CC4UWidget):
    WIDGET_TYPE = "project_notes"
    WIDGET_TITLE = "PROJECT NOTES"
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._notes: str = ""
        self._editing: bool = False

    def on_mount(self) -> None:
        data = state_module.load_widget_data("project_notes")
        self._notes = data.get("notes", "")

    def render_content(self) -> str:
        if not self._notes:
            return "[dim]No notes — click to add[/dim]"
        return self._notes

    def on_click(self, event) -> None:
        if self._editing:
            return
        self._editing = True
        try:
            self.query_one("#widget-body", Static).display = False
        except Exception:
            pass
        ta = TextArea(
            text=self._notes,
            id="notes-area",
        )
        self.mount(ta)
        self.mount(Static("[dim]Esc to save[/dim]", id="notes-hint"))
        self.call_after_refresh(self._focus_area)

    def _focus_area(self) -> None:
        try:
            self.query_one("#notes-area", TextArea).focus()
        except Exception:
            pass

    def on_key(self, event) -> None:
        if event.key == "escape" and self._editing:
            try:
                value = self.query_one("#notes-area", TextArea).text
                self._commit(value)
            except Exception:
                self._commit(self._notes)

    def _commit(self, value: str) -> None:
        self._editing = False
        self._notes = value
        state_module.save_widget_data("project_notes", {"notes": self._notes})
        try:
            self.query_one("#notes-area", TextArea).remove()
        except Exception:
            pass
        try:
            self.query_one("#notes-hint", Static).remove()
        except Exception:
            pass
        try:
            body = self.query_one("#widget-body", Static)
            body.display = True
            body.update(self.render_content())
        except Exception:
            pass
