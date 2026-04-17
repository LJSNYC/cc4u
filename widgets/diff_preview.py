import os
import subprocess
from widgets.base import CC4UWidget

_WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}


class DiffPreviewWidget(CC4UWidget):
    WIDGET_TYPE = "diff_preview"
    WIDGET_TITLE = "DIFF PREVIEW"
    STATE_KEYS = ["tools"]

    def on_mount(self) -> None:
        super().on_mount()
        self._poll_state()

    def render_content(self) -> str:
        tools = self.data.get("tools", [])
        if not tools:
            return "[dim]No changes[/dim]"
        for entry in reversed(tools):
            if entry.get("tool") in _WRITE_TOOLS:
                inp = entry.get("input", {})
                path = inp.get("file_path") or inp.get("notebook_path") or ""
                name = os.path.basename(path) if path else "?"
                lines = [f"[bold]{name}[/bold]"]
                diff = self._git_diff(path) if path else ""
                if diff:
                    for line in diff.splitlines()[:12]:
                        if line.startswith("+") and not line.startswith("+++"):
                            lines.append(f"[green]{line}[/green]")
                        elif line.startswith("-") and not line.startswith("---"):
                            lines.append(f"[red]{line}[/red]")
                        elif line.startswith("@@"):
                            lines.append(f"[dim]{line}[/dim]")
                else:
                    lines.append(f"[dim]{entry.get('tool', '?')} — no tracked diff[/dim]")
                return "\n".join(lines)
        return "[dim]No recent edits[/dim]"

    @staticmethod
    def _git_diff(path: str) -> str:
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", "--", path],
                capture_output=True, text=True, timeout=2,
                cwd=os.path.dirname(os.path.abspath(path)) or ".",
            )
            return result.stdout.strip()
        except Exception:
            return ""
