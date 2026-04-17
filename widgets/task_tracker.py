import state as state_module
from textual.widgets import Static, Input
from widgets.base import CC4UWidget


class TaskTrackerWidget(CC4UWidget):
    WIDGET_TYPE = "task_tracker"
    WIDGET_TITLE = "TASKS"
    STATE_KEYS = []

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._tasks: list = []
        self._adding: bool = False

    def on_mount(self) -> None:
        data = state_module.load_widget_data("task_tracker")
        self._tasks = data.get("tasks", [])

    def render_content(self) -> str:
        if not self._tasks:
            return "[dim]No tasks — click [bold]+[/bold] to add[/dim]"
        done = sum(1 for t in self._tasks if t.get("done"))
        total = len(self._tasks)
        lines = [f"[dim]{done}/{total} done[/dim]"]
        for task in self._tasks:
            mark = "[green]✓[/green]" if task.get("done") else "○"
            text = task.get("text", "")
            style = "[dim]" if task.get("done") else ""
            end = "[/dim]" if task.get("done") else ""
            lines.append(f"{mark} {style}{text}{end}")
        lines.append("[dim]+ add task[/dim]")
        return "\n".join(lines)

    def on_click(self, event) -> None:
        if self._adding:
            return
        body_offset = 1  # title row
        # Last visible row is the "+ add task" hint
        add_row = body_offset + len(self._tasks) + 1
        if event.y >= add_row:
            self._start_add()
            return
        idx = max(0, min(event.y - body_offset - 1, len(self._tasks) - 1))
        if 0 <= idx < len(self._tasks):
            self._tasks[idx]["done"] = not self._tasks[idx].get("done", False)
            state_module.save_widget_data("task_tracker", {"tasks": self._tasks})
            self._refresh_body()

    def _start_add(self) -> None:
        self._adding = True
        inp = Input(placeholder="New task…", id="task-input")
        self.mount(inp)
        self.call_after_refresh(self._focus_input)

    def _focus_input(self) -> None:
        try:
            self.query_one("#task-input", Input).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._tasks.append({"text": text, "done": False})
            state_module.save_widget_data("task_tracker", {"tasks": self._tasks})
        self._stop_add()

    def on_key(self, event) -> None:
        if event.key == "escape" and self._adding:
            self._stop_add()

    def _stop_add(self) -> None:
        self._adding = False
        try:
            self.query_one("#task-input", Input).remove()
        except Exception:
            pass
        self._refresh_body()

    def _refresh_body(self) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass
