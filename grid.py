from __future__ import annotations

WIDGET_REGISTRY: dict[str, type] = {}


def register(widget_cls):
    """Decorator — registers a widget class by its WIDGET_TYPE."""
    WIDGET_REGISTRY[widget_cls.WIDGET_TYPE] = widget_cls
    return widget_cls


def build_widget(cfg: dict):
    """Instantiate the right CC4UWidget subclass from a config entry."""
    wtype = cfg.get("type", "")
    cls = WIDGET_REGISTRY.get(wtype)
    if cls is None:
        from widgets.base import CC4UWidget
        class _Unknown(CC4UWidget):
            WIDGET_TYPE = wtype
            WIDGET_TITLE = wtype.upper()
            def render_content(self): return f"[dim]unknown: {wtype}[/dim]"
        cls = _Unknown
    return cls(cfg=cfg, id=f"widget-{wtype}-{id(cfg)}")
