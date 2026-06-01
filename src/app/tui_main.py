"""Entry point for the local text build (Versions 1-2, v3 P1).

The composition root: it wires the concrete dependencies (config, repository,
llm) into the brain `Engine`, then hands the engine to the TUI adapter. This is
the only place the TUI's dependencies are constructed.
"""

from __future__ import annotations


def main() -> None:
    """Build the brain and launch the Vani text UI."""
    from src.config.config import Config
    from src.contracts.documents import migrate
    from src.engine import Engine
    from src.llm.client import AnthropicClient
    from src.state.json_store import JsonStore
    from src.tui.app import run_tui

    config = Config.load()
    repository = JsonStore(config.state_dir, migrator=migrate)
    llm = AnthropicClient(config)
    engine = Engine(repository, llm)
    run_tui(engine)


if __name__ == "__main__":
    main()
