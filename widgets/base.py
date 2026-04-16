from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

import state as state_module


class CC4UWidget(Widget):
    """
    Base class for all CC4U dashboard widgets.

    Subclasses must implement render_content() → str.
    Widgets fill their WidgetSlot container; edit-mode controls are
    handled by the parent WidgetSlot, not by the widget itself.
    """

    DEFAULT_CSS = """
    CC4UWidget {
        border: solid $widget-border;
        background: $surface;
        overflow: hidden hidden;
        padding: 0 1;
        height: 100%;
    }
    """

    WIDGET_TYPE: str = "base"
    WIDGET_TITLE: str = "Widget"
    REFRESH_RATE: float = 2.0
    STATE_KEYS: list[str] = []

    data: reactive[dict] = reactive({})

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(**kwargs)
        self.cfg = cfg
        self.add_class("cc4u-widget")

    def on_mount(self) -> None:
        self.set_interval(self.REFRESH_RATE, self._poll_state)

    def _poll_state(self) -> None:
        fresh = {}
        if "session" in self.STATE_KEYS:
            fresh["session"] = state_module.session()
        if "git" in self.STATE_KEYS:
            fresh["git"] = state_module.git()
        if "tools" in self.STATE_KEYS:
            fresh["tools"] = state_module.tools()
        self.data = fresh

    def watch_data(self, new_data: dict) -> None:
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        return "--"

    def compose(self) -> ComposeResult:
        yield Static(self.WIDGET_TITLE, id="widget-title", classes="widget-title")
        try:
            _body = self.render_content()
        except Exception:
            _body = ""
        yield Static(_body, id="widget-body", classes="widget-body")
