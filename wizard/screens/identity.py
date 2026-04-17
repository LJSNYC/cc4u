# cc4u/wizard/screens/identity.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input
from textual.binding import Binding


class IdentityScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, initial_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self._initial_name = initial_name

    def compose(self) -> ComposeResult:
        yield Static("[bold]What should CC4U call you?[/bold]\n")
        yield Input(
            value=self._initial_name,
            placeholder="Your name (max 24 chars)",
            max_length=24,
            id="name-input",
        )
        yield Static("\n[dim]Press Enter to continue[/dim]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip() or "user"
        self.dismiss(name)

    def action_back(self) -> None:
        self.dismiss(None)
