# cc4u/wizard/screens/layout_preset.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, RadioSet, RadioButton, Button
from textual.binding import Binding

PRESETS = {
    "balanced": {
        "label": "Balanced",
        "desc": "Claude Code center · widgets on sides",
        "widgets": [
            {"type": "pty_pane",     "col": 2, "row": 0, "col_span": 8, "row_span": 6},
            {"type": "clock",        "col": 0, "row": 0, "col_span": 2, "row_span": 1},
            {"type": "git_status",   "col": 0, "row": 1, "col_span": 2, "row_span": 3},
            {"type": "cost_tracker", "col": 0, "row": 4, "col_span": 2, "row_span": 2},
            {"type": "pomodoro",     "col": 10,"row": 0, "col_span": 2, "row_span": 2},
            {"type": "cpu_memory",   "col": 10,"row": 2, "col_span": 2, "row_span": 2},
        ],
    },
    "minimal": {
        "label": "Minimal",
        "desc": "Claude Code with just a status bar",
        "widgets": [
            {"type": "pty_pane", "col": 0, "row": 0, "col_span": 12, "row_span": 6},
        ],
    },
    "power": {
        "label": "Power User",
        "desc": "Widgets everywhere, Claude Code center-left",
        "widgets": [
            {"type": "pty_pane",     "col": 2, "row": 0, "col_span": 5, "row_span": 5},
            {"type": "clock",        "col": 0, "row": 0, "col_span": 2, "row_span": 1},
            {"type": "git_status",   "col": 0, "row": 1, "col_span": 2, "row_span": 2},
            {"type": "pomodoro",     "col": 0, "row": 3, "col_span": 2, "row_span": 2},
            {"type": "cost_tracker", "col": 7, "row": 0, "col_span": 2, "row_span": 2},
            {"type": "cpu_memory",   "col": 9, "row": 0, "col_span": 3, "row_span": 3},
        ],
    },
}


class LayoutPresetScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("[bold]Choose a starting layout[/bold]\n[dim]You can rearrange everything later with Ctrl+E[/dim]\n")
        with RadioSet(id="preset-radio"):
            for key, preset in PRESETS.items():
                yield RadioButton(f"{preset['label']} — {preset['desc']}", id=f"preset-{key}")
        yield Static("")
        yield Button("Continue →", id="continue-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-btn":
            radio_set = self.query_one("#preset-radio", RadioSet)
            selected = radio_set.pressed_button
            if selected:
                key = selected.id.replace("preset-", "")
                self.dismiss(PRESETS[key]["widgets"])
            else:
                self.dismiss(PRESETS["balanced"]["widgets"])

    def action_back(self) -> None:
        self.dismiss(None)
