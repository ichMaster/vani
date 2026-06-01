"""The version comes from version.yaml (single source of truth) — VANI follow-up."""

from pathlib import Path

import src
from src.version import get_version

VERSION_YAML = Path(__file__).parents[2] / "version.yaml"


def _yaml_version() -> str:
    for raw in VERSION_YAML.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    raise AssertionError("no version in version.yaml")


def test_version_yaml_exists():
    assert VERSION_YAML.exists()


def test_get_version_matches_yaml():
    assert get_version() == _yaml_version()


def test_package_version_is_current():
    assert src.__version__ == "0.1.0"
