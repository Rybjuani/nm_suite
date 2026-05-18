from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path


def _log_dir() -> Path:
    appdata = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    log_dir = Path(appdata) / "NeuroMood" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup(app_name: str) -> Path:
    """Instala sys.excepthook y FileHandler para capturar crashes en %APPDATA%/NeuroMood/logs/."""
    log_path = _log_dir() / f"{app_name}.log"

    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8", mode="a"),
        ],
    )

    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.error(
            "Unhandled exception:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
    return log_path
