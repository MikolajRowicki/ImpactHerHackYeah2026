"""Tiny helper to read settings from the environment.

Every name that is read is recorded in USED, so a test can check that
.env.example lists all of them.
"""

import os
from pathlib import Path

USED: set[str] = set()

_TRUE = {"1", "true", "yes", "on"}


def get(name: str, default: str = "") -> str:
    USED.add(name)
    return os.environ.get(name, default)


def flag(name: str, default: bool = False) -> bool:
    value = get(name)
    if value == "":
        return default
    return value.strip().lower() in _TRUE


def load_dotenv(path: Path) -> None:
    """Load KEY=value lines from a .env file. Variables already set win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("\"'")
        os.environ.setdefault(key.strip(), value)
