"""Tests for config + .env loading (precedence: env var > .env > default)."""

from src.config.config import Config


def test_reads_api_key_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-from-dotenv\n", encoding="utf-8")
    config = Config.load(env_file=str(env))
    assert config.anthropic_api_key == "sk-from-dotenv"


def test_real_env_overrides_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-real-env")
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-from-dotenv\n", encoding="utf-8")
    config = Config.load(env_file=str(env))
    assert config.anthropic_api_key == "sk-from-real-env"


def test_reading_dotenv_does_not_mutate_os_environ(tmp_path, monkeypatch):
    import os

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-leak-check\n", encoding="utf-8")
    Config.load(env_file=str(env))
    assert "ANTHROPIC_API_KEY" not in os.environ


def test_missing_key_is_none(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = Config.load(env_file=str(tmp_path / "does-not-exist.env"))
    assert config.anthropic_api_key is None
    assert config.log_level == "INFO"


def test_overrides_win(tmp_path):
    config = Config.load(env_file=str(tmp_path / "none.env"), anthropic_api_key="explicit")
    assert config.anthropic_api_key == "explicit"
