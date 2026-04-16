import json
import os
from pathlib import Path

THEMES_DIR = Path(__file__).parent / "data" / "themes"
TCSS_OUTPUT = "/tmp/cc4u/theme.tcss"


def list_themes() -> list[str]:
    """List all available theme names."""
    return sorted(p.stem for p in THEMES_DIR.glob("*.json"))


def load_theme(name: str) -> dict:
    """Load a theme from JSON file."""
    path = THEMES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Theme not found: {name}")
    with open(path) as f:
        return json.load(f)


def to_textual_theme(name: str):
    """Build a Textual ``Theme`` object from a cc4u theme JSON file."""
    from textual.theme import Theme
    c = load_theme(name).get("colors", {})
    return Theme(
        name=name,
        primary=c.get("accent_primary",   "#0178D4"),
        secondary=c.get("border",          "#004578"),
        warning=c.get("accent_warn",       "#FEA62B"),
        error=c.get("accent_danger",       "#B93C5B"),
        success=c.get("accent_secondary",  "#4EBF71"),
        accent=c.get("accent_primary",     "#FEA62B"),
        foreground=c.get("text_primary",   "#E0E0E0"),
        background=c.get("bg_primary",     "#121212"),
        surface=c.get("bg_widget",         "#1E1E1E"),
        panel=c.get("status_bar_bg",       "#242F38"),
        dark=True,
        variables={
            "primary-background": c.get("status_bar_bg", "#242F38"),
            # Theme-specific widget border color (always distinct from bg)
            "widget-border": c.get("border", "#444444"),
        },
    )


def write_tcss(name: str, path: str = TCSS_OUTPUT) -> None:
    """Write a minimal marker TCSS (kept for wizard compatibility)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"/* cc4u theme: {name} */\n")


def apply(name: str, app) -> None:
    """Switch to *name* on the running Textual app via the Theme API."""
    app.theme = name
