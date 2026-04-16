from widgets.base import CC4UWidget


class TokenUsageWidget(CC4UWidget):
    WIDGET_TYPE = "token_usage"
    WIDGET_TITLE = "TOKENS"
    STATE_KEYS = ["session"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        s = self.data.get("session", {})
        if not s:
            return "[dim]No data[/dim]"
        inp = s.get("tokens_input", 0)
        out = s.get("tokens_output", 0)
        cache = s.get("tokens_cache_read", 0)
        total = inp + out

        def fmt(n: int) -> str:
            return f"{n:,}" if n < 10_000 else f"{n / 1000:.1f}k"

        return (
            f"In:    [cyan]{fmt(inp)}[/cyan]\n"
            f"Out:   [green]{fmt(out)}[/green]\n"
            f"Cache: [yellow]{fmt(cache)}[/yellow]\n"
            f"Total: [bold]{fmt(total)}[/bold]"
        )
