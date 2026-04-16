from __future__ import annotations
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Static, Button
from textual.message import Message  # used by _EditBtn.Pressed
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
import config as cfg_module
import themes as themes_module
import state as state_module
from grid import build_widget, WIDGET_REGISTRY
import widgets  # side-effect: populates WIDGET_REGISTRY
from widgets.pty_pane import PtyPane


class _EditBtn(Static):
    """Slim clickable button for edit-mode controls. Static-based so it renders at height:1."""

    class Pressed(Message):
        def __init__(self, btn: "_EditBtn") -> None:
            super().__init__()
            self.btn = btn

    def on_click(self) -> None:
        self.post_message(self.Pressed(self))


class WidgetSlot(Widget):
    """Wraps one CC4UWidget. _weight controls its fr height within a ColumnContainer."""

    DEFAULT_CSS = """
    WidgetSlot { width: 100%; height: 1fr; layout: vertical; }
    """

    def __init__(self, wtype: str, weight: int = 1, **kwargs):
        super().__init__(**kwargs)
        self._wtype = wtype
        self._weight = weight
        self._inner = None

    def on_mount(self) -> None:
        self.styles.height = f"{self._weight}fr"
        self._inner = build_widget({"type": self._wtype})
        self.mount(self._inner)

    def set_weight(self, w: int) -> None:
        self._weight = max(1, w)
        self.styles.height = f"{self._weight}fr"

    def swap_widget(self, new_type: str) -> None:
        """Replace the inner widget with a new type."""
        if self._inner is not None:
            self._inner.remove()
        self._wtype = new_type
        swap_btns = list(self.query(".swap-btn"))
        new_w = build_widget({"type": new_type})
        self._inner = new_w
        if swap_btns:
            self.mount(new_w, before=swap_btns[0])
        else:
            self.mount(new_w)

    def show_edit_controls(self) -> None:
        if not self.query(".swap-btn"):
            self.mount(_EditBtn("⟳ swap", classes="swap-btn"))
        if not self.query(".move-up-btn"):
            self.mount(_EditBtn("↑", classes="move-up-btn"))
        if not self.query(".move-down-btn"):
            self.mount(_EditBtn("↓", classes="move-down-btn"))
        if not self.query(".remove-btn"):
            self.mount(_EditBtn("✕ remove", classes="remove-btn"))

    def hide_edit_controls(self) -> None:
        for cls in (".swap-btn", ".move-up-btn", ".move-down-btn", ".remove-btn"):
            for b in self.query(cls):
                b.remove()


class ColumnContainer(Widget):
    """Left or right sidebar — vertical stack of WidgetSlots."""

    DEFAULT_CSS = """
    ColumnContainer { layout: vertical; height: 100%; }
    """

    _counter: int = 0  # global counter — ensures slot IDs are always unique after removes

    def __init__(self, side: str, widget_types: list, heights: list, **kwargs):
        super().__init__(**kwargs)
        self._side = side
        self._widget_types = list(widget_types)
        self._heights = list(heights)

    def compose(self) -> ComposeResult:
        for wtype, weight in zip(self._widget_types, self._heights):
            ColumnContainer._counter += 1
            yield WidgetSlot(wtype, weight, id=f"slot-{self._side}-{ColumnContainer._counter}")

    def get_slots(self) -> list:
        return list(self.query(WidgetSlot))

    def get_widget_types(self) -> list:
        return [s._wtype for s in self.get_slots()]

    def get_heights(self) -> list:
        return [s._weight for s in self.get_slots()]

    def add_widget_slot(self, wtype: str) -> None:
        ColumnContainer._counter += 1
        self.mount(WidgetSlot(wtype, 1, id=f"slot-{self._side}-{ColumnContainer._counter}"))


class StatusBtn(Static):
    """Clickable label that works at height:1 (Button doesn't)."""

    DEFAULT_CSS = """
    StatusBtn {
        width: auto;
        padding: 0 1;
        color: $accent;
        background: $primary-background;
        height: 1;
    }
    StatusBtn:hover {
        background: $accent;
        color: $background;
    }
    StatusBtn.-active-btn {
        background: $warning;
        color: $background;
    }
    """

    def on_click(self) -> None:
        _actions = {
            "btn-edit": "action_toggle_edit_mode",
            "btn-add": "action_open_widget_picker",
            "btn-theme": "action_cycle_theme",
        }
        action = _actions.get(self.id)
        if action:
            getattr(self.app, action)()


class StatusBar(Widget):
    """Bottom strip: action buttons left, info right."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary-background;
        layout: horizontal;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield StatusBtn("EDIT", id="btn-edit")
        yield StatusBtn("+", id="btn-add")
        yield StatusBtn("THEME", id="btn-theme")
        yield Static(
            "[dim]⟳ swap widget · ↑↓ reorder[/dim]",
            id="edit-hint",
        )
        yield Static("", id="status-info")

    def on_mount(self) -> None:
        try:
            self.query_one("#edit-hint", Static).display = False
        except Exception:
            pass
        self._update_info()
        self.set_interval(2.0, self._update_info)

    def _update_info(self) -> None:
        s = state_module.session()
        g = state_module.git()
        cost = s.get("cost_usd", 0.0)
        branch = g.get("branch", "")
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        info = f"${cost:.4f}  {s.get('tokens_input', 0) + s.get('tokens_output', 0)} tok"
        if branch:
            info += f"  [dim]{branch}[/dim]"
        info += f"  {now}"
        try:
            self.query_one("#status-info", Static).update(info)
        except Exception:
            pass

    def set_edit_mode(self, active: bool) -> None:
        """Toggle EDIT ↔ DONE label and show/hide the edit hint."""
        try:
            btn = self.query_one("#btn-edit", StatusBtn)
            btn.update("DONE" if active else "EDIT")
            if active:
                btn.add_class("-active-btn")
            else:
                btn.remove_class("-active-btn")
        except Exception:
            pass
        try:
            self.query_one("#edit-hint", Static).display = active
        except Exception:
            pass

    def set_theme_label(self, name: str) -> None:
        try:
            self.query_one("#btn-theme", StatusBtn).update(f"◈ {name}")
        except Exception:
            pass


class WidgetPickerModal(ModalScreen):
    """Floating modal to add or swap a widget."""

    DEFAULT_CSS = """
    WidgetPickerModal { align: center middle; }
    WidgetPickerModal > .picker-container {
        width: 40; height: 26; background: $surface; border: solid $accent; padding: 1 2;
    }
    """

    def __init__(self, unused_types: list, title: str = "Select Widget", **kwargs):
        super().__init__(**kwargs)
        self._types = unused_types
        self._modal_title = title

    def compose(self) -> ComposeResult:
        with Widget(classes="picker-container"):
            yield Static(f"[bold]{self._modal_title}[/bold]\n[dim]Click to select[/dim]\n")
            with VerticalScroll():
                for wtype in self._types:
                    label = wtype.replace("_", " ").title()
                    yield Button(label, id=f"pick-{wtype}")
            yield Button("Cancel", id="pick-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pick-cancel":
            self.dismiss(None)
        elif event.button.id and event.button.id.startswith("pick-"):
            self.dismiss(event.button.id[len("pick-"):])


class CC4UApp(App):
    """Main CC4U dashboard application."""

    CSS_PATH = ["cc4u.tcss"]
    TITLE = "CC4U"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self, config: dict, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self._edit_mode = False
        import os, glob as _glob
        theme_dir = os.path.join(os.path.dirname(__file__), "data", "themes")
        self._themes = sorted([
            os.path.splitext(os.path.basename(p))[0]
            for p in _glob.glob(os.path.join(theme_dir, "*.json"))
        ])
        current = config.get("theme", "tactical")
        self._theme_idx = self._themes.index(current) if current in self._themes else 0

    def get_css_variables(self) -> dict:
        """Provide fallback for $widget-border before any theme is registered."""
        base = super().get_css_variables()
        base.setdefault("widget-border", "#444444")
        return base

    def compose(self) -> ComposeResult:
        left_widgets = self.config.get("left_widgets", [])
        right_widgets = self.config.get("right_widgets", [])
        left_heights = self.config.get("left_heights", [1] * len(left_widgets))
        right_heights = self.config.get("right_heights", [1] * len(right_widgets))
        cmd = self.config.get("behavior", {}).get("pty_command", "claude")
        with Horizontal(id="main-layout"):
            yield ColumnContainer("left", left_widgets, left_heights, id="left-col")
            yield PtyPane(cfg={"type": "pty_pane", "pty_command": cmd}, id="pty-pane")
            yield ColumnContainer("right", right_widgets, right_heights, id="right-col")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._register_themes()
        self.theme = self.config.get("theme", "tactical")
        self._apply_col_widths()

    def _register_themes(self) -> None:
        for name in themes_module.list_themes():
            try:
                self.register_theme(themes_module.to_textual_theme(name))
            except Exception:
                pass

    def _apply_col_widths(self) -> None:
        left_w = self.config.get("left_col_width", 16)
        right_w = self.config.get("right_col_width", 16)
        try:
            self.query_one("#left-col").styles.width = f"{left_w}%"
        except Exception:
            pass
        try:
            self.query_one("#right-col").styles.width = f"{right_w}%"
        except Exception:
            pass

    def action_cycle_theme(self) -> None:
        if not self._themes:
            return
        self._theme_idx = (self._theme_idx + 1) % len(self._themes)
        name = self._themes[self._theme_idx]
        self.config["theme"] = name
        cfg_module.save(self.config)
        self.theme = name
        try:
            self.query_one("#status-bar", StatusBar).set_theme_label(name)
        except Exception:
            pass

    def action_toggle_edit_mode(self) -> None:
        self._edit_mode = not self._edit_mode
        try:
            self.query_one("#status-bar", StatusBar).set_edit_mode(self._edit_mode)
        except Exception:
            pass
        for slot in self.query(WidgetSlot):
            if self._edit_mode:
                slot.show_edit_controls()
            else:
                slot.hide_edit_controls()
        if self._edit_mode:
            self.add_class("edit-mode")
        else:
            self.remove_class("edit-mode")
            self._save_layout()

    def _save_layout(self) -> None:
        try:
            left_col = self.query_one("#left-col", ColumnContainer)
            right_col = self.query_one("#right-col", ColumnContainer)
            self.config["left_widgets"] = left_col.get_widget_types()
            self.config["right_widgets"] = right_col.get_widget_types()
            self.config["left_heights"] = left_col.get_heights()
            self.config["right_heights"] = right_col.get_heights()
        except Exception:
            pass
        cfg_module.save(self.config)

    def action_open_widget_picker(self) -> None:
        used = {"pty_pane", "base"}
        for col_id in ("#left-col", "#right-col"):
            try:
                col = self.query_one(col_id, ColumnContainer)
                used.update(col.get_widget_types())
            except Exception:
                pass
        unused = [t for t in WIDGET_REGISTRY if t not in used]
        if not unused:
            self.notify("All widgets are already in use.", severity="warning", timeout=3)
            return

        try:
            lc = len(self.query_one("#left-col", ColumnContainer).get_slots())
            rc = len(self.query_one("#right-col", ColumnContainer).get_slots())
            both_full = lc >= 6 and rc >= 6
        except Exception:
            both_full = False

        if both_full:
            self.notify(
                "Both columns are full (6 widgets each). Pick a new widget, then choose which one to replace.",
                severity="information",
                timeout=5,
            )
            # Step 1: pick new type. Step 2: pick which existing slot to replace.
            def _on_pick_new(new_type: str | None) -> None:
                if not new_type:
                    return
                all_slots = list(self.query(WidgetSlot))
                slot_labels = [s._wtype.replace("_", " ").title() for s in all_slots]
                slot_types = [s._wtype for s in all_slots]

                def _on_pick_replace(replace_type: str | None) -> None:
                    if not replace_type:
                        return
                    for s in self.query(WidgetSlot):
                        if s._wtype == replace_type:
                            s.swap_widget(new_type)
                            self._save_layout()
                            return

                self.push_screen(
                    WidgetPickerModal(slot_types, title="Replace Which Widget?"),
                    _on_pick_replace,
                )

            self.push_screen(WidgetPickerModal(unused, title="Add Widget (replaces existing)"), _on_pick_new)
            return

        def _on_pick(wtype: str | None) -> None:
            if not wtype:
                return
            try:
                left_col = self.query_one("#left-col", ColumnContainer)
                right_col = self.query_one("#right-col", ColumnContainer)
                lc = len(left_col.get_slots())
                rc = len(right_col.get_slots())
                if lc >= 6 and rc >= 6:
                    self.notify("Both columns are full.", severity="warning", timeout=3)
                    return
                target = left_col if (lc <= rc and lc < 6) else right_col
                # Defensive: if chosen target is already full, use the other side
                if len(target.get_slots()) >= 6:
                    target = right_col if target is left_col else left_col
                target.add_widget_slot(wtype)
                self._save_layout()
            except Exception as e:
                self.notify(f"Could not add widget: {e}", severity="error")

        self.push_screen(WidgetPickerModal(unused, title="Add Widget"), _on_pick)

    async def on__edit_btn_pressed(self, event: _EditBtn.Pressed) -> None:
        btn = event.btn
        slot = btn.parent
        if not isinstance(slot, WidgetSlot):
            return
        if "swap-btn" in btn.classes:
            self._open_swap_modal(slot)
        elif "move-up-btn" in btn.classes:
            self._move_slot(slot, -1)
        elif "move-down-btn" in btn.classes:
            self._move_slot(slot, 1)
        elif "remove-btn" in btn.classes:
            await slot.remove()  # await so _save_layout sees the updated DOM
            self._save_layout()
        event.stop()

    def _open_swap_modal(self, slot: WidgetSlot) -> None:
        used = {s._wtype for s in self.query(WidgetSlot)} | {"pty_pane", "base"}
        unused = [t for t in WIDGET_REGISTRY if t not in used]
        if not unused:
            self.notify("All widget types are already in use.", severity="warning", timeout=3)
            return

        def _on_swap(new_type: str | None) -> None:
            if not new_type:
                return
            slot.swap_widget(new_type)
            self._save_layout()

        self.push_screen(
            WidgetPickerModal(unused, title=f"Swap {slot._wtype.replace('_', ' ').title()}"),
            _on_swap,
        )

    def _move_slot(self, slot: WidgetSlot, direction: int) -> None:
        col = slot.parent
        if not isinstance(col, ColumnContainer):
            return
        slots = col.get_slots()
        idx = slots.index(slot)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(slots):
            return
        neighbor = slots[new_idx]
        # Swap types and weights
        slot._wtype, neighbor._wtype = neighbor._wtype, slot._wtype
        slot._weight, neighbor._weight = neighbor._weight, slot._weight
        slot.swap_widget(slot._wtype)
        neighbor.swap_widget(neighbor._wtype)
        slot.set_weight(slot._weight)
        neighbor.set_weight(neighbor._weight)
        self._save_layout()

