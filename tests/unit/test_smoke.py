"""Smoke test: the package and its sub-packages import cleanly."""

import importlib


def test_package_version() -> None:
    import src

    assert src.__version__


def test_subpackages_import() -> None:
    for name in (
        "src.config.config",
        "src.engine",
        "src.app.tui_main",
    ):
        assert importlib.import_module(name)
