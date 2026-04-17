# cc4u/wizard/app.py
from __future__ import annotations
from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Static
import config as cfg_module
from wizard.screens.welcome import WelcomeScreen
from wizard.screens.identity import IdentityScreen
from wizard.screens.layout_preset import LayoutPresetScreen, PRESETS
from wizard.screens.widget_picker import WidgetPickerScreen
from wizard.screens.theme_picker import ThemePickerScreen


class WizardApp(App):
    """Onboarding wizard — runs if no config.json exists."""

    CSS = """
    Screen {
        align: center middle;
        padding: 2 4;
    }
    Button { margin: 1 0; }
    RadioSet { height: auto; max-height: 20; }
    """

    TITLE = "CC4U Setup"

    def __init__(self, existing_config: Optional[dict] = None, **kwargs):
        super().__init__(**kwargs)
        self._cfg = existing_config or cfg_module.default_config()
        self.result_config: Optional[dict] = None
        # Preserve wizard state across back-navigation
        self._wiz_name: str = self._cfg.get("user_name", "")
        self._wiz_preset: str = ""
        self._wiz_widgets: list = []

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen(), self._after_welcome)

    def _after_welcome(self, result) -> None:
        if result:
            self.push_screen(IdentityScreen(initial_name=self._wiz_name), self._after_identity)
        else:
            self.exit()

    def _after_identity(self, name) -> None:
        if name is None:
            self.push_screen(WelcomeScreen(), self._after_welcome)
            return
        self._wiz_name = name or "user"
        self._cfg["user_name"] = self._wiz_name
        self.push_screen(LayoutPresetScreen(initial_preset=self._wiz_preset), self._after_layout)

    def _after_layout(self, result) -> None:
        if result is None:
            self.push_screen(IdentityScreen(initial_name=self._wiz_name), self._after_identity)
            return
        preset_key, widgets = result
        self._wiz_preset = preset_key
        self._cfg["widgets"] = widgets
        # On first forward pass, pre-populate picker with preset's sidebar widgets.
        # On back-nav, restore whatever the user had previously selected.
        if not self._wiz_widgets:
            self._wiz_widgets = [w["type"] for w in widgets if w["type"] != "pty_pane"]
        self.push_screen(WidgetPickerScreen(initial_types=self._wiz_widgets), self._after_widget_picker)

    def _after_widget_picker(self, selected_types) -> None:
        if selected_types is None:
            self.push_screen(LayoutPresetScreen(initial_preset=self._wiz_preset), self._after_layout)
            return
        self._wiz_widgets = selected_types
        self._cfg["_selected_widget_types"] = selected_types
        self.push_screen(ThemePickerScreen(initial_theme=self._cfg.get("theme", "tactical")), self._after_theme)

    def _after_theme(self, theme) -> None:
        if theme is None:
            self.push_screen(WidgetPickerScreen(initial_types=self._wiz_widgets), self._after_widget_picker)
            return
        self._cfg["theme"] = theme

        # Read the preset's pty_pane position so auto_layout can honour it
        # (balanced keeps pty at cols 2-9; power keeps it at cols 2-6; etc.).
        preset_widgets = self._cfg.get("widgets", [])
        pty_cfg = next((w for w in preset_widgets if w["type"] == "pty_pane"), None)
        pty_col      = pty_cfg.get("col",      2) if pty_cfg else 2
        pty_col_span = pty_cfg.get("col_span", 8) if pty_cfg else 8

        # Build the ordered type list: preset order first, then any NEW extras
        # from the widget picker that aren't already in the preset.
        picker_types = self._cfg.pop("_selected_widget_types", [])
        seen: set = set()
        all_types: list = []
        for t in [w["type"] for w in preset_widgets] + picker_types:
            if t not in seen:
                seen.add(t)
                all_types.append(t)

        # auto_layout distributes everything cleanly, respecting the preset's pty
        # position and auto-scaling sidebar widget heights for large widget counts.
        layout = cfg_module.auto_layout(
            all_types, pty_col=pty_col, pty_col_span=pty_col_span
        )
        self._cfg.update(layout)
        self._cfg.pop("widgets", None)  # remove the scratch "widgets" key set earlier

        cfg_module.save(self._cfg)
        self.result_config = self._cfg
        self.exit()
