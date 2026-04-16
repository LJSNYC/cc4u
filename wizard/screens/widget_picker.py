# cc4u/wizard/screens/widget_picker.py
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static, Checkbox, Button
from textual.binding import Binding

# (wtype, label, default_checked, description)
ALL_WIDGETS = [
    ("clock",          "Clock",          True,
     "Live clock showing the current time. Updates every second. Great for a top-corner slot."),
    ("git_status",     "Git Status",     True,
     "Current branch, staged / unstaged file counts, and latest commit hash. Polls every 2 s."),
    ("cost_tracker",   "Cost Tracker",   True,
     "Running USD cost and total token count for the active Claude session."),
    ("pomodoro",       "Pomodoro Timer", True,
     "25/5 Pomodoro timer. Click to start or pause. Notifies you when each interval ends."),
    ("cpu_memory",     "CPU / Memory",   True,
     "System CPU percentage and RAM usage. Lightweight — updates every 2 s."),
    ("tool_log",       "Tool Log",       False,
     "Live log of every tool Claude invokes: file reads, edits, bash commands, searches, etc."),
    ("session_status", "Session Status", False,
     "Claude session health at a glance: model name, context window fill %, active tool count."),
    ("token_usage",    "Token Usage",    False,
     "Detailed token breakdown — input, output, cache reads and writes for this session."),
    ("diff_preview",   "Diff Preview",   False,
     "Live unified diff of the most recent file Claude edited, updated after every tool call."),
    ("daily_goal",     "Daily Goal",     False,
     "Displays your focus goal for the day. Set it by editing ~/.config/cc4u/widget_data/daily_goal.json."),
    ("quote",          "Quote",          False,
     "Rotating motivational or technical quote from your quotes library. Advances every 5 minutes."),
    ("file_watcher",   "File Watcher",   False,
     "Watches your working directory for file changes and lists the most recently modified files."),
    ("network",        "Network",        False,
     "Live network throughput — bytes sent and received per second on your active interface."),
    ("uptime",         "Uptime",         False,
     "Elapsed time since this CC4U session started, plus overall system uptime."),
    ("session_log",    "Session Log",    False,
     "Scrollable log of Claude assistant turns and output messages for the current session."),
    ("dir_tree",       "Dir Tree",       False,
     "File tree of your current working directory. Useful for navigating large projects quickly."),
    ("word_count",     "Word Count",     False,
     "Counts words in recently edited files. Handy for writing, docs, or markdown-heavy work."),
    ("checklist",      "Checklist",      False,
     "Persistent checklist with check-off. State is saved between sessions in a JSON file."),
    ("quick_links",    "Quick Links",    False,
     "One-click shortcuts to URLs or local paths. Configure links in quick_links.json."),
    ("project_notes",  "Project Notes",  False,
     "Sticky-note area for freeform project context. Edit project_notes.json to update it."),
    ("git_log",        "Git Log",        False,
     "Last 10 git commits with short hash, author, and message. Refreshes every 5 s."),
    ("git_branches",   "Git Branches",   False,
     "Lists all local git branches and highlights the currently checked-out one."),
    ("session_timer",  "Session Timer",  False,
     "Simple wall-clock timer counting elapsed time since CC4U launched."),
    ("task_tracker",   "Task Tracker",   False,
     "Lightweight task list — click any task to toggle it done. State persists to JSON."),
]

_DESC_MAP = {wtype: (label, desc) for wtype, label, _, desc in ALL_WIDGETS}


class WidgetPickerScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    CSS = """
    WidgetPickerScreen {
        align: center middle;
    }
    #picker-box {
        width: 76;
        height: 34;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
        layout: vertical;
    }
    #picker-header {
        height: 2;
        color: $text;
    }
    #picker-columns {
        height: 1fr;
        margin-bottom: 1;
    }
    #picker-left {
        width: 32;
        border-right: solid $primary-background;
        padding-right: 1;
    }
    #picker-right {
        width: 1fr;
        padding: 0 0 0 2;
    }
    #desc-name {
        color: $accent;
        text-style: bold;
        height: 2;
    }
    #desc-body {
        height: 1fr;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-box"):
            yield Static(
                "[bold]Choose your widgets[/bold]  "
                "[dim]Tab/click to select · focus a checkbox to preview[/dim]",
                id="picker-header",
            )
            with Horizontal(id="picker-columns"):
                with VerticalScroll(id="picker-left"):
                    for wtype, label, default, _ in ALL_WIDGETS:
                        yield Checkbox(label, value=default, id=f"cb-{wtype}")
                with Vertical(id="picker-right"):
                    yield Static("", id="desc-name")
                    yield Static(
                        "[dim]Focus a checkbox on the left\nto preview the widget here.[/dim]",
                        id="desc-body",
                    )
            yield Button("Continue →", id="continue-btn", variant="primary")

    def on_mount(self) -> None:
        # Pre-populate description with the first checked widget.
        for wtype, _, default, _ in ALL_WIDGETS:
            if default:
                self._show_desc(wtype)
                break

    # Focus events don't bubble to Screen — use Checkbox.Changed (fires on every
    # click/space-toggle) and watch_focused (fires on Tab navigation).

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Update description whenever a checkbox is clicked or space-toggled."""
        cb = event.checkbox
        if getattr(cb, "id", None) and cb.id.startswith("cb-"):
            self._show_desc(cb.id[3:])

    def watch_focused(self, focused) -> None:
        """Update description when Tab-navigation lands on a checkbox."""
        if focused is not None and getattr(focused, "id", None):
            fid = str(focused.id)
            if fid.startswith("cb-"):
                self._show_desc(fid[3:])

    def _show_desc(self, wtype: str) -> None:
        label, desc = _DESC_MAP.get(wtype, ("", ""))
        try:
            self.query_one("#desc-name", Static).update(f"[bold]{label}[/bold]")
            self.query_one("#desc-body", Static).update(desc)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-btn":
            selected = []
            for wtype, _, _, _ in ALL_WIDGETS:
                cb = self.query_one(f"#cb-{wtype}", Checkbox)
                if cb.value:
                    selected.append(wtype)
            self.dismiss(selected)

    def action_back(self) -> None:
        self.dismiss(None)
