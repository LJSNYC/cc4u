# CC4U — Claude Code For You

A terminal dashboard that wraps [Claude Code](https://claude.ai/code) in a customizable widget UI. Built with Python + [Textual](https://github.com/Textualize/textual).

```
  ██████╗ ██████╗ ██╗  ██╗██╗   ██╗
 ██╔════╝██╔════╝ ██║  ██║██║   ██║
 ██║     ██║      ███████║██║   ██║
 ██║     ██║      ╚════██║██║   ██║
 ╚██████╗╚██████╗      ██║╚██████╔╝
  ╚═════╝ ╚═════╝      ╚═╝ ╚═════╝
```

Instead of running `claude` in a plain terminal, run `cc4u` — you get a live Claude Code session surrounded by the widgets you care about.

---

## Install

```bash
git clone https://github.com/LJSNYC/cc4u.git ~/cc4u
cd ~/cc4u
bash install.sh
```

> Clone to a permanent location (like `~/cc4u`). The installer pins the `cc4u` command to wherever you clone — moving or deleting the folder will break it.

Then launch:

```bash
cc4u
```

First run opens the onboarding wizard (name → layout → widgets → theme). After that, `cc4u` goes straight to your dashboard.

**Reset wizard:**
```bash
rm ~/.config/cc4u/config.json && cc4u
```

---

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.10 |
| Claude Code CLI | latest |
| git | ≥ 2.x |

---

## Layout

Three-column layout: left sidebar · Claude Code PTY · right sidebar.

```
┌─────────────┬─────────────────────────┬─────────────┐
│  left col   │                         │  right col  │
│  widgets    │    Claude Code (PTY)    │  widgets    │
│             │                         │             │
└─────────────┴─────────────────────────┴─────────────┘
         [EDIT]  [+]  [THEME]   $0.0000  0 tok  main  23:00
```

---

## Widgets (25 built-in)

| Category | Widgets |
|---|---|
| Claude Code | Cost Tracker, Token Usage, Session Status, Session Timer, Tool Log |
| Git | Git Status, Git Log, Git Branches, Diff Preview |
| Project | Project Notes, Quick Links, Dir Tree, File Watcher |
| System | CPU/Memory, Network, Clock, Uptime |
| Productivity | Daily Goal, Task Tracker, Checklist, Pomodoro, Word Count |
| Fun | Quote of the Day |
| Meta | Session Log |

---

## Themes (19 built-in)

Amber, Blueprint, Catppuccin, Cyberpunk, Dracula, Forest, Glass, Gruvbox, Hacker, High-Contrast, Midnight, Monochrome, Nord, Obsidian, Sakura, Solarized, Synthwave, Tactical, Tokyo-Night.

Switch themes live with the **THEME** button in the status bar.

---

## Edit Mode

Press **EDIT** in the status bar to rearrange your layout:

- **⟳ swap** — replace a widget with any unused one
- **↑ / ↓** — reorder widgets within a column
- **✕ remove** — remove a widget
- **+** — add a widget to any open slot

Press **DONE** to save.

---

## Onboarding Wizard

Five screens: Welcome → Name → Layout preset → Widget picker → Theme picker.

Three layout presets: **Balanced** (equal sidebars), **Minimal** (thin sidebars), **Power** (wide sidebars).

---

## Development

```bash
# Run from source
cd cc4u
python3 -m cc4u

# Tests
python3 -m pytest tests/ -q
```

---

## Project Structure

```
cc4u/
├── cc4u.py              # Entry point
├── __main__.py          # python -m cc4u support
├── app.py               # CC4UApp, layout, StatusBar, edit mode
├── grid.py              # WIDGET_REGISTRY, build_widget()
├── config.py            # load/save, auto_layout()
├── state.py             # /tmp/cc4u/*.json reader + widget_data/
├── themes.py            # 19 themes → Textual Theme objects
├── cc4u.tcss            # Stylesheet
├── widgets/             # 25 widget modules
├── wizard/              # Onboarding wizard (5 screens)
│   └── screens/
├── hooks/               # Claude Code hook scripts
├── data/
│   ├── themes/          # 19 JSON theme files
│   ├── quotes.json
│   └── pricing.json
├── tests/
├── bin/cc4u             # CLI launcher
└── install.sh           # One-step installer
```

---

## License

MIT
