# cc4u/wizard/screens/theme_picker.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, RadioSet, RadioButton, Button
from textual.binding import Binding
import themes as themes_module


class ThemePickerScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        available = themes_module.list_themes()
        yield Static("[bold]Choose a theme[/bold]\n")
        with RadioSet(id="theme-radio"):
            for name in available:
                try:
                    t = themes_module.load_theme(name)
                    tagline = t.get("tagline", "")
                    label = f"{name}  [dim]{tagline}[/dim]" if tagline else name
                except Exception:
                    label = name
                yield RadioButton(label, id=f"theme-{name}", value=(name == "tactical"))
        yield Static("")
        yield Button("Launch →", id="launch-btn", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch-btn":
            radio_set = self.query_one("#theme-radio", RadioSet)
            selected = radio_set.pressed_button
            if selected:
                theme = selected.id.replace("theme-", "")
            else:
                theme = "tactical"
            self.dismiss(theme)

    def action_back(self) -> None:
        self.dismiss(None)
