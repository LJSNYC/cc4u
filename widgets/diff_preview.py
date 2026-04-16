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
                path = inp.get("file_path") or inp.get("notebook_path") or "?"
                result = str(entry.get("result", ""))
                import os
                name = os.path.basename(path)
                lines = [f"[bold]{name}[/bold]"]
                for line in result.splitlines()[:6]:
                    if line.startswith("+"):
                        lines.append(f"[green]{line}[/green]")
                    elif line.startswith("-"):
                        lines.append(f"[red]{line}[/red]")
                    else:
                        lines.append(f"[dim]{line}[/dim]")
                return "\n".join(lines)
        return "[dim]No recent edits[/dim]"
