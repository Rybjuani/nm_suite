from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path


import re

_PII_PATTERNS = [r"@\S+\.\S+", r"\bpat_[A-Za-z0-9]{8,}\b"]
_APPDATA_DIRS = {
    "hub": "NeuroMoodHub",
    "suite": "NeuroMood",
}


def redact(text: str) -> str:
    """Redacts PII from text before logging."""
    for pattern in _PII_PATTERNS:
        text = re.sub(pattern, "<redacted>", text)
    return text


def _log_dir(app_name: str) -> Path:
    appdata = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    app_dir = _APPDATA_DIRS.get(app_name.lower(), "NeuroMood")
    log_dir = Path(appdata) / app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _has_file_handler(root: logging.Logger, log_path: Path) -> bool:
    target = log_path.resolve()
    for handler in root.handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        try:
            if Path(handler.baseFilename).resolve() == target:
                return True
        except OSError:
            continue
    return False


def _startup_record(app_name: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="NeuroMood.CrashLog",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="Crash logging initialized for %s",
        args=(app_name,),
        exc_info=None,
    )


def setup(app_name: str) -> Path:
    """Instala sys.excepthook y FileHandler para capturar crashes en AppData."""
    log_path = _log_dir(app_name) / f"{app_name}.log"

    root = logging.getLogger()
    root.setLevel(logging.ERROR)
    if not _has_file_handler(root, log_path):
        file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        root.addHandler(file_handler)
        file_handler.handle(_startup_record(app_name))

    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        root.error(
            redact(
                "Unhandled exception:\n"
                + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            )
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
    return log_path
