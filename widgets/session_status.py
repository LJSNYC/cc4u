from widgets.base import CC4UWidget


class SessionStatusWidget(CC4UWidget):
    WIDGET_TYPE = "session_status"
    WIDGET_TITLE = "SESSION STATUS"
    STATE_KEYS = ["session"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        s = self.data.get("session", {})
        if not s:
            return "[dim]No session data[/dim]"
        state = s.get("claude_state", "idle")
        last_tool = s.get("last_tool", "--")
        idle_since = s.get("idle_since", "")
        color = {"running": "green", "idle": "yellow", "error": "red"}.get(state, "white")
        lines = [
            f"State: [{color}]{state}[/{color}]",
            f"Tool:  [dim]{last_tool}[/dim]",
        ]
        if idle_since:
            ts = str(idle_since)[11:19]  # HH:MM:SS from ISO datetime
            lines.append(f"Idle:  [dim]{ts}[/dim]")
        return "\n".join(lines)
