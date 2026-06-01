"""Headless replay: drive full conversations through the brain, no live API (VANI-010)."""

import asyncio

from src.contracts.documents import Session


def test_replay_drives_a_full_conversation(make_engine, tmp_store):
    engine = make_engine(["hi there", "tell me more"])

    async def run() -> None:
        await engine.handle_turn("s1", "hello")
        await engine.handle_turn("s1", "more?")

    asyncio.run(run())

    session = Session.from_dict(tmp_store.load("sessions", "s1"))
    assert [(t.role, t.text) for t in session.turns] == [
        ("user", "hello"),
        ("assistant", "hi there"),
        ("user", "more?"),
        ("assistant", "tell me more"),
    ]


def test_replay_uses_no_live_calls(make_engine):
    engine = make_engine(["scripted reply"])
    reply = asyncio.run(engine.handle_turn("s1", "hi"))
    assert reply == "scripted reply"


def test_sample_session_fixture_roundtrips(sample_session):
    assert Session.from_dict(sample_session.to_dict()) == sample_session
