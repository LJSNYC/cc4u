import json
import random
from pathlib import Path
from textual.widgets import Static
from widgets.base import CC4UWidget

QUOTES_FILE = str(Path(__file__).parent.parent / "data" / "quotes.json")


class QuoteWidget(CC4UWidget):

    def __init__(self, cfg: dict, **kwargs):
        super().__init__(cfg, **kwargs)
        self._quotes: list = []
        self._idx: int = 0
    WIDGET_TYPE = "quote"
    WIDGET_TITLE = "QUOTE"
    REFRESH_RATE = 300.0  # rotate every 5 minutes
    STATE_KEYS = []

    def on_mount(self) -> None:
        try:
            with open(QUOTES_FILE) as f:
                data = json.load(f)
                # Handle nested structure (dict with categories) or flat list
                if isinstance(data, dict):
                    self._quotes = []
                    for category_quotes in data.values():
                        if isinstance(category_quotes, list):
                            self._quotes.extend(category_quotes)
                elif isinstance(data, list):
                    self._quotes = data
                else:
                    self._quotes = []
        except (OSError, json.JSONDecodeError):
            self._quotes = []
        self._idx = random.randint(0, max(0, len(self._quotes) - 1))
        self.set_interval(self.REFRESH_RATE, self._advance)

    def _advance(self) -> None:
        if self._quotes:
            self._idx = (self._idx + 1) % len(self._quotes)
        try:
            self.query_one("#widget-body", Static).update(self.render_content())
        except Exception:
            pass

    def render_content(self) -> str:
        if not self._quotes:
            return "[dim]No quotes loaded[/dim]"
        q = self._quotes[self._idx]
        text = q.get("text", "")
        author = q.get("author", "")
        return f'[italic]"{text}"[/italic]\n[dim]— {author}[/dim]' if author else f'[italic]"{text}"[/italic]'
