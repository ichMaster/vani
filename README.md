# Vani

**A living-personality voice companion.** Vani is designed not as a "query → response" function but as a single, coherent presence: it is born to fit the user at onboarding, has a stable character, wakes with a daily mood, adapts its manner to the user, carries a running conversation, and builds a model of the person over time — yet always speaks as one voice.

> **Status: specification only.** This repository currently holds the design documents. There is no implementation code yet — the system is planned in Python (see the roadmap). The first build task is the `v1 P0` skeleton.

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
specification/            # English design documents
  requirements/           # the master specification ("what")
  architecture/           # solution architecture ("how")
    schemas/              # JSON Schema for state documents + pipeline contracts
  roadmap/                # implementation roadmap ("when")
  missions/               # the long-form concept article
docs/
  requirements_ukr/       # Ukrainian originals (.uk.md / .uk.docx)
.claude/skills/           # repo automation: upload-issues, execute-issues, release-version
```

The documents exist in **English** (`specification/`) and **Ukrainian** (`docs/requirements_ukr/`); English is authoritative. When changing a spec, update both and bump the version in the header.

## Planned tech stack

- **Versions 1–2 and v3 P1 (local):** Python (`.venv` + `pyproject.toml`), `pytest` + `ruff`, Textual (TUI), the Anthropic SDK (Haiku/Opus), a local LLM fallback (Gemma/Qwen) for offline turns, skyfield (astro), asyncio, local JSON state; from v3 P1, Whisper (ASR) + Piper-Ukrainian (TTS).
- **v3 P2:** FastAPI + WebSocket server, MongoDB.
- **v3 P3:** AtomS3R + Echo Pyramid with xiaozhi firmware, Opus audio codec.

## License

[MIT](LICENSE) © 2026 ichMaster
