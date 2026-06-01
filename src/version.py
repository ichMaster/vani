"""Read the application version from version.yaml (the single source of truth).

Parsed without PyYAML so importing the package — including for the packaging
metadata (`pyproject` reads `src.__version__`) — never requires runtime deps.
"""

from __future__ import annotations

from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent.parent / "version.yaml"


def get_version() -> str:
    """Return the `version:` value from version.yaml, or '0.0.0' if unavailable."""
    try:
        for raw in _VERSION_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return "0.0.0"
