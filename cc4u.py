"""
CC4U — Claude Code 4 You dashboard.
Usage:
    python -m cc4u           # launch (wizard if no config, else dashboard)
    python -m cc4u --setup   # force wizard
"""
import sys
import os

# Add cc4u/ to path so all modules resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg_module
from pathlib import Path


def main():
    args = sys.argv[1:]
    force_setup = "--setup" in args

    if force_setup or not Path(cfg_module.CONFIG_PATH).exists():
        _run_wizard()
    else:
        _run_dashboard(cfg_module.load())


def _run_wizard():
    from wizard.app import WizardApp
    existing = cfg_module.load() if Path(cfg_module.CONFIG_PATH).exists() else None
    app = WizardApp(existing_config=existing)
    app.run()
    if app.result_config:
        _run_dashboard(app.result_config)


def _run_dashboard(config: dict):
    from app import CC4UApp
    CC4UApp(config=config).run()


if __name__ == "__main__":
    main()
