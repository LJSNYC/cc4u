from widgets.base import CC4UWidget


class GitStatusWidget(CC4UWidget):
    WIDGET_TYPE = "git_status"
    WIDGET_TITLE = "GIT"
    STATE_KEYS = ["git"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        g = self.data.get("git", {})
        if not g:
            return "[dim]--[/dim]"
        branch = g.get("branch", "?")
        staged = g.get("staged", 0)
        unstaged = g.get("unstaged", 0)
        untracked = g.get("untracked", 0)
        ahead = g.get("ahead", 0)
        behind = g.get("behind", 0)
        msg = g.get("last_commit_msg", "")[:30]

        sync = ""
        if ahead:
            sync += f" [green]↑{ahead}[/green]"
        if behind:
            sync += f" [red]↓{behind}[/red]"

        lines = [
            f"[bold cyan]{branch}[/bold cyan]{sync}",
            f"[green]+{staged}[/green] [yellow]~{unstaged}[/yellow] [dim]?{untracked}[/dim]",
            f"[dim]{msg}[/dim]" if msg else "",
        ]
        return "\n".join(l for l in lines if l)
