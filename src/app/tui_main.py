"""Entry point for the local text build (Versions 1-2, v3 P1).

A thin adapter that launches the TUI over the brain engine. The full TUI is
built in VANI-006; this keeps the console-script entry point importable.
"""

from __future__ import annotations


def main() -> None:
    """Launch the Vani text UI."""
    from src.tui.app import run_tui  # lazy: TUI deps load on demand

    run_tui()


if __name__ == "__main__":
    main()
