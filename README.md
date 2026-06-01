# Vani

**A living-personality voice companion.** Vani is designed not as a "query → response" function but as a single, coherent presence: it is born to fit the user at onboarding, has a stable character, wakes with a daily mood, adapts its manner to the user, carries a running conversation, and builds a model of the person over time — yet always speaks as one voice.

> **Status: early build (v0.0.1).** Version 1, Phase 0 — the local text-chat skeleton — is implemented under `src/`: a transport-agnostic brain (`engine`), the repository + JSON store, versioned data contracts, a streaming Anthropic client, a synchronous guardrail, a placeholder canon, telemetry, and a Textual TUI. The remaining phases (planner, personality layers, voice, server, device) are still design documents — see the [roadmap](specification/roadmap/roadmap-v0.2.en.md).

## Getting started

Requires **Python 3.11+** and an **Anthropic API key**.

```bash
git clone https://github.com/ichMaster/vani.git
cd vani
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env            # then add your key to .env:
#   ANTHROPIC_API_KEY=sk-ant-...

vani                            # launch the text chat (TUI)
```

The API key is read from `.env` (gitignored) or the environment — a real env var wins over `.env`. Conversation history is stored locally under `.vani_state/`.

### Development

```bash
pytest            # run the test suite (incl. a headless, network-free replay)
ruff check .      # lint
ruff format .     # format
```

## The idea

- **One personality, four layers.** A stable character *canon*; a daily *temperament*; *active facets* (internal advisors that come forward by topic and mood); and *delivery* (mirroring the user's style within bounded daily drift). Multiplicity lives in the reasoning — the voice stays one.
- **A mostly-deterministic planner.** The LLM is touched at only two points per turn — perception (understand the message) and generation (speak). Everything between is scored code: fast, predictable, tunable, and cheap. Two LLM tiers: **Haiku** (fast: perception + simple replies) and **Opus 4.8** (deep reasoning).
- **A synchronous Guardian.** Hard invariants — correctness, honesty, safety, wellbeing, child safety — stand above identity and are checked before anything is spoken.
- **A model of the interlocutor.** A two-layer portrait with a curiosity cycle, and a cross-cutting *confidence* attribute on almost everything the assistant infers.

The target hardware is an M5Stack Echo Pyramid terminal talking to an orchestration server, but the whole "brain" runs locally first as a text app and gains voice, a server, and the device later.

## Roadmap at a glance

Work is delivered in three product **versions** (phases are reprioritized by review score, so the highest-value cognitive machinery is built and validated first):

| Version | Phases | Focus |
|---|---|---|
| **Version 1** — Cognitive core (text) | P0–P4 | planner, conversation line, portrait + confidence, background pass |
| **Version 2** — Personality layers (text) | P1–P6 | canon, astro + temperament, onboarding, weighted facets + Guardian, delivery, memory |
| **Version 3** — Voice, server, device | P1–P3 | voice (ASR/TTS), server + MongoDB, hardware |

Cross-references use the form `vN Pk` (e.g. `v2 P4`). Full detail in the [roadmap](specification/roadmap/roadmap-v0.2.en.md).

## Where to start

The design is captured in three documents — a "what / how / when" triad:

- **What** → [Master Specification (v1.8)](specification/requirements/specification-v1.8.en.md) — the authoritative spec: layers, planner pipeline, facets, conversation line, portrait, confidence, Guardian, state model.
- **How** → [Solution Architecture (v0.2)](specification/architecture/architecture-v0.1.en.md) — module layout, data contracts, the brain/transport boundary (API-readiness), error handling, security, testing.
- **When** → [Implementation Roadmap (v0.4)](specification/roadmap/roadmap-v0.2.en.md) — the three versions and their phases.

Background reading: [the concept article](specification/missions/vani-article.en.md) — the academic framing, the scientific-grounding analysis, and six peer reviews. Data shapes: [JSON Schemas](specification/architecture/schemas/) for every state document and pipeline contract.

## Repository layout

```
src/                      # the application (v1 P0): engine, state, contracts, llm,
                          #   guardian, core, telemetry, config, tui, app
tests/                    # pytest suite (unit) + replay/ (headless harness)
pyproject.toml            # deps + ruff/pytest config; `vani` entry point
specification/            # English design documents
  requirements/           # the master specification ("what")
  architecture/           # solution architecture ("how")
    schemas/              # JSON Schema for state documents + pipeline contracts
  roadmap/                # implementation roadmap ("when") + implementation-v1/ issues
  missions/               # the long-form concept article
docs/
  requirements_ukr/       # Ukrainian originals (.uk.md / .uk.docx)
.claude/skills/           # repo automation: upload-issues, execute-issues, release-version
```

The documents exist in **English** (`specification/`) and **Ukrainian** (`docs/requirements_ukr/`); English is authoritative. When changing a spec, update both and bump the version in the header.

## Tech stack

- **In place (v1 P0, local):** Python 3.11+ (`.venv` + `pyproject.toml`), Textual (TUI), the Anthropic SDK, `python-dotenv`, local JSON state, `pytest` + `ruff`.
- **Planned for the rest of Versions 1–2 and v3 P1 (local):** skyfield (astro), a local LLM fallback (Gemma/Qwen) for offline turns; from v3 P1, Whisper (ASR) + Piper-Ukrainian (TTS).
- **v3 P2:** FastAPI + WebSocket server, MongoDB.
- **v3 P3:** AtomS3R + Echo Pyramid with xiaozhi firmware, Opus audio codec.

## License

[MIT](LICENSE) © 2026 ichMaster
