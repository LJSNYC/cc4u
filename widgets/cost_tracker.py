from widgets.base import CC4UWidget


class CostTrackerWidget(CC4UWidget):
    WIDGET_TYPE = "cost_tracker"
    WIDGET_TITLE = "COST"
    STATE_KEYS = ["session"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        s = self.data.get("session", {})
        if not s:
            return "[dim]--[/dim]"
        cost = s.get("cost_usd", 0.0)
        inp = s.get("tokens_input", 0)
        out = s.get("tokens_output", 0)
        cache_r = s.get("tokens_cache_read", 0)

        def fmt_k(n: int) -> str:
            return f"{n/1000:.1f}k" if n >= 1000 else str(n)

        color = "green" if cost < 0.05 else "yellow" if cost < 0.20 else "red"
        lines = [
            f"[bold {color}]${cost:.4f}[/bold {color}]",
            f"in [cyan]{fmt_k(inp)}[/cyan]  out [cyan]{fmt_k(out)}[/cyan]",
            f"[dim]cache {fmt_k(cache_r)}[/dim]" if cache_r else "",
        ]
        return "\n".join(l for l in lines if l)
