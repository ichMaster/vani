# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This is a **specification-only repository**. There is no implementation code yet — only design documents under `specification/`. The `.gitignore` is Python-oriented because the system is planned to be built in Python (see roadmap), but no source tree, package config, build, lint, or test tooling exists. Do not invent build/test commands; there are none until v1 P0 scaffolding is created.

The first implementation task (roadmap v1 P0) is to scaffold the Python project under a `src/` package with the module layout defined in the architecture doc, choose dependency/packaging/lint tooling, and stand up the `Repository` interface + `json_store`.

## What Vani is

A single, coherent "living personality" voice companion. One personality, not a committee — multiplicity lives in the reasoning, the voice stays one. Target hardware is an M5Stack Echo Pyramid terminal talking to an orchestration server, but the system is built locally first (text TUI → voice → server → device). Two LLM tiers: **Haiku** (fast: perception + simple replies) and **Opus 4.8** (deep reasoning). Specs are written in both English and Ukrainian.

## Document map (read these to understand the system)

`specification/` holds the **English** documents in a category-first taxonomy (`architecture/`, `requirements/`, `roadmap/`, `missions/`). The original **Ukrainian** documents live flat under `docs/requirements_ukr/` at the repo root. The three core documents form a deliberate "what / how / when" triad — keep them consistent when editing:

- `specification/requirements/specification-v1.8.en.md` — **the "what."** Authoritative master spec. Defines the four personality layers, the per-turn planner pipeline, facets, conversation line, portrait, confidence, Guardian, state model (§13), and config knobs (§18). Start here.
- `specification/architecture/architecture-v0.1.en.md` — **the "how."** The `src/` module layout (§2), module responsibilities (§3), state documents, and tech stack by phase (§8).
- `specification/roadmap/roadmap-v0.2.en.md` — **the "when."** Three delivery versions — v1 (phases P0–P4), v2 (P1–P6), v3 (P1–P3) — each phase with goal/scope/modules/tasks/definition-of-done, plus six review-driven refinements mapped to phases (§3). Cross-references use `vN Pk` (e.g. `v2 P4`).

Each English doc has a Ukrainian original under `docs/requirements_ukr/` (`.uk.md` / `.uk.docx`). `specification/missions/vani-article.en.md` is a longer research-style article on the overall concept (the academic framing, scientific-grounding table, and six peer reviews), translated from the Ukrainian original at `docs/requirements_ukr/vani-article.uk.md`. **When changing a spec, update both the English (`specification/`) and Ukrainian (`docs/requirements_ukr/`) versions** so they stay in sync, and bump the version number in the header. English is treated as authoritative.

## Core architecture concepts (span multiple sections — internalize before coding)

**One personality, four layers** (spec §2). All four feed a single planner that emits one voice:
1. **Character core / canon** (`core/`) — stable character bible compiled into a cached identity-prompt prefix. Derived from the natal chart chosen at onboarding.
2. **Daily temperament** (`astro/`) — mood from astrological transits, mapped to five dials: energy, warmth, verbosity, imagination, caution.
3. **Active facets** (`facets/`) — internal advisors (Analyst, Nurturing Parent, Skeptic, Guardian, etc.) with activation weights by topic + mood. Internal-only facets modify content but never become the voice.
4. **Delivery** (`delivery/`) — the length/register envelope mirrored from the user, plus bounded daily fluctuation.

**The planner is mostly deterministic code, not LLM calls** (spec §9). The LLM touches only two points per turn: perception (Haiku, structured classification of the input) and generation (Haiku or Opus). Everything between — facet weights, strategy selection, routing, state updates, post-update — is scored code (microseconds), tunable via config knobs. A typical deep turn = exactly one small Haiku call + one Opus call.

**One Opus call with weighted facets** (spec §11), not one call per facet. Multiple active facets are passed as weighted emphasis in a single prompt; Opus integrates all sides into one coherent response. Coherence is guaranteed by construction; cost stays 1×.

**Background pass is async and non-blocking** (spec §9.6, §12). The fast path responds immediately because audio is irreversible; a separate cheap-tier async task then validates policy decisions, grows the user portrait, and generates curiosity questions — affecting *subsequent* turns, never the current one. Has `shadow` (telemetry-only) and `active` (soft, inertial state corrections) modes.

**The Guardian is a synchronous gate, always before speaking** (spec §9.6, §19). Safety cannot be checked after the fact (no rollback on audio). The async background pass refines taste/policy only — it never replaces the synchronous Guardian. Hard invariants (correctness, honesty, safety, wellbeing, child safety) stand above identity: gender, wounds, and "dark" facets color tone but never weaken safety or competence.

**Confidence is a cross-cutting attribute** (spec §9.7) on nearly every state element (emotion, intent, facet weights, style profile, loops, portrait hypotheses): it rises with confirmation, decays over time, and drives decisions (low confidence → ask again / be cautious / mirror less). **Exception:** the canon and hard invariants carry no confidence — they are foundation, not hypothesis.

**State lives behind a repository interface** (architecture §4). `state/repository.py` is the single access point; `json_store.py` backs it through v3 P1, `mongo_store.py` from v3 P2. No personality layer knows which store sits beneath it — this is what makes the eventual JSON→Mongo swap a one-module change. The same logical documents (`canon`, `users`, `portrait`, `conversation_line`, `question_bank`, `material`, `sessions`, `telemetry`, `validation_log`) exist at every stage.

**The brain is constant; only transport and storage change across phases.** Personality layers, planner, background pass, and Guardian are identical whether running in the local TUI (Versions 1–2 and v3 P1), behind a WebSocket server (v3 P2), or driving the physical device (v3 P3).

## Phase-ordering note

The roadmap is **reprioritized by review scores**, not by dependency-natural order: the high-value cognitive machinery (planner, conversation line, portrait+confidence, background pass — Version 1, v1 P1–P4) is built *before* canon, astro, onboarding, facets, and delivery (Version 2, v2 P1–P5). Consequence: early phases run with a thin placeholder canon, plain-text delivery, and only a minimal safety gate; these are filled in during Version 2 (the full Guardian arrives at v2 P4). Check the current version and phase before assuming a layer is fully implemented.

## Versioning convention

Release versions are `a.b.c`:

- **`a` — global version:** the delivery Version from the roadmap (1, 2, or 3).
- **`b` — phase:** the phase number within that version (P0, P1, …).
- **`c` — fix:** incremented for fixes/patches released after that phase shipped.

So each phase milestone is `a.b.0`, and post-phase fixes bump `c`. Examples: v1 P0 → `1.0.0`; v1 P1 → `1.1.0`; a fix after v1 P1 → `1.1.1`; v2 P3 → `2.3.0`; v3 P3 → `3.3.0`.

Note: the initial bootstrap tags (`0.0.1`, `0.1.0`) predate this convention; it applies from here. (The `execute-issues` skill's older "Phase N → 0.N.0" note is superseded by this scheme.)

## Planned tech stack (per architecture §8)

- **Versions 1–2 and v3 P1 (local):** Python, Textual (TUI), Anthropic SDK (Haiku/Opus), skyfield/kerykeion (astro charts), asyncio, local JSON state. From v3 P1: faster-whisper (ASR) + Piper-Ukrainian (TTS).
- **v3 P2:** FastAPI + WebSocket server, MongoDB.
- **v3 P3:** AtomS3R + Echo Pyramid with xiaozhi firmware, Opus audio codec.
