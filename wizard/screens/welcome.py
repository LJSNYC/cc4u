# cc4u/wizard/screens/welcome.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.binding import Binding

LOGO = """
 ██████╗ ██████╗ ██╗  ██╗██╗   ██╗
██╔════╝██╔════╝ ██║  ██║██║   ██║
██║     ██║      ███████║██║   ██║
██║     ██║      ╚════██║██║   ██║
╚██████╗╚██████╗      ██║╚██████╔╝
 ╚═════╝ ╚═════╝      ╚═╝ ╚═════╝
Claude Code, turned into an app.
"""


class WelcomeScreen(Screen):
    BINDINGS = [Binding("enter", "next", "Start")]

    def compose(self) -> ComposeResult:
        yield Static(LOGO, id="logo")
        yield Static("[dim]Press Enter to begin setup[/dim]")
        yield Button("Get Started →", id="start-btn", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.action_next()

    def action_next(self) -> None:
        self.dismiss(True)
