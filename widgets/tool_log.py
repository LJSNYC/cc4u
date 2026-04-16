from widgets.base import CC4UWidget

_MAX_ENTRIES = 8


class ToolLogWidget(CC4UWidget):
    WIDGET_TYPE = "tool_log"
    WIDGET_TITLE = "TOOL LOG"
    STATE_KEYS = ["tools"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        tools = self.data.get("tools", [])
        if not tools:
            return "[dim]No tool calls[/dim]"
        lines = []
        for entry in tools[-_MAX_ENTRIES:]:
            tool = entry.get("tool", "?")
            at = str(entry.get("at", ""))
            time_str = at[11:19] if len(at) >= 19 else at
            lines.append(f"[dim]{time_str}[/dim] [cyan]{tool}[/cyan]")
        return "\n".join(reversed(lines))
