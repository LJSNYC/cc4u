from widgets.base import CC4UWidget


class GitLogWidget(CC4UWidget):
    WIDGET_TYPE = "git_log"
    WIDGET_TITLE = "GIT LOG"
    STATE_KEYS = ["git"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        g = self.data.get("git", {})
        if not g:
            return "[dim]No git data[/dim]"
        branch = g.get("branch", "?")
        msg = g.get("last_commit_msg", "--")
        ahead = g.get("ahead", 0)
        behind = g.get("behind", 0)
        lines = [f"[bold green]{branch}[/bold green]"]
        if ahead:
            lines.append(f"[yellow]↑ {ahead} ahead[/yellow]")
        if behind:
            lines.append(f"[red]↓ {behind} behind[/red]")
        lines.append(f"[dim]{msg[:50]}[/dim]")
        return "\n".join(lines)
