import state as state_module
from textual.widgets import Static, Input
from widgets.base import CC4UWidget


class DailyGoalWidget(CC4UWidget):
    WIDGET_TYPE = "daily_goal"
    WIDGET_TITLE = "DAILY GOAL"
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._goal: str = ""
        self._editing: bool = False

    def on_mount(self) -> None:
        data = state_module.load_widget_data("daily_goal")
        self._goal = data.get("goal", "")

    def render_content(self) -> str:
        if not self._goal:
            return "[dim]No goal set — click to add one[/dim]"
        return f"[bold]{self._goal}[/bold]"

    def on_click(self, event) -> None:
        if self._editing:
            return
        self._editing = True
        try:
            self.query_one("#widget-body", Static).display = False
        except Exception:
            pass
        inp = Input(
            value=self._goal,
            placeholder="Today's goal…",
            id="goal-input",
        )
        self.mount(inp)
        self.call_after_refresh(self._focus_input)

    def _focus_input(self) -> None:
        try:
            self.query_one("#goal-input", Input).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._commit(event.value)

    def on_key(self, event) -> None:
        if event.key == "escape" and self._editing:
            self._commit(self._goal)  # revert

    def _commit(self, value: str) -> None:
        self._editing = False
        self._goal = value.strip()
        state_module.save_widget_data("daily_goal", {"goal": self._goal})
        try:
            self.query_one("#goal-input", Input).remove()
        except Exception:
            pass
        try:
            body = self.query_one("#widget-body", Static)
            body.display = True
            body.update(self.render_content())
        except Exception:
            pass
