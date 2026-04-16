from widgets.base import CC4UWidget


class GitBranchesWidget(CC4UWidget):
    WIDGET_TYPE = "git_branches"
    WIDGET_TITLE = "GIT BRANCHES"
    STATE_KEYS = ["git"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        g = self.data.get("git", {})
        if not g:
            return "[dim]No git data[/dim]"
        branch = g.get("branch", "?")
        staged = g.get("staged", 0)
        unstaged = g.get("unstaged", 0)
        untracked = g.get("untracked", 0)
        ahead = g.get("ahead", 0)
        behind = g.get("behind", 0)
        lines = [f"[bold green]{branch}[/bold green]"]
        if ahead:
            lines.append(f"[yellow]↑ {ahead} ahead[/yellow]")
        if behind:
            lines.append(f"[red]↓ {behind} behind[/red]")
        if staged:
            lines.append(f"[green]● {staged} staged[/green]")
        if unstaged:
            lines.append(f"[yellow]○ {unstaged} modified[/yellow]")
        if untracked:
            lines.append(f"[dim]? {untracked} untracked[/dim]")
        if not (staged or unstaged or untracked or ahead or behind):
            lines.append("[dim]clean[/dim]")
        return "\n".join(lines)
