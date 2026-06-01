# Version 0, Phase 0 — Chat Skeleton (TUI): GitHub Issues

Decomposes roadmap `v0 P0` into implementable issues. IDs are continuous across Version 0 phases (`VANI-001`…). Labels follow the `upload-issues` skill: `p0::phase:0`, `p0::size:*`, `p0::stage:*`.

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | VANI-001 | Project scaffold and tooling | S | 1 — Foundation | -- |
| 2 | VANI-002 | Repository interface and json_store | S | 1 — Foundation | VANI-001 |
| 3 | VANI-003 | Data contracts and versioned schemas | M | 1 — Foundation | VANI-002 |
| 4 | VANI-004 | LLM client (Opus, streaming) | S | 2 — Brain & LLM | VANI-001 |
| 5 | VANI-005 | Transport-agnostic engine | M | 2 — Brain & LLM | VANI-002, VANI-004 |
| 6 | VANI-006 | TUI loop and transcript persistence | M | 3 — Interface | VANI-005, VANI-003 |
| 7 | VANI-007 | Minimal guardrail pass (placeholder Guardian) | S | 4 — Identity & Safety | VANI-005 |
| 8 | VANI-008 | Placeholder canon and confidence scaffolding | S | 4 — Identity & Safety | VANI-003 |
| 9 | VANI-009 | Logging and telemetry scaffolding | S | 4 — Identity & Safety | VANI-001 |
| 10 | VANI-010 | pytest harness and headless replay | M | 5 — Testing | VANI-005 |

**Size legend:** S = 1–2 days, M = 3–5 days, L = 5–8 days

---

## Dependency Tree

```
VANI-001 (scaffold)
   |-- VANI-002 (repository) -- VANI-003 (contracts + schemas) -- VANI-008 (canon + confidence)
   |-- VANI-004 (llm client)
   |-- VANI-009 (logging/telemetry)

VANI-002 + VANI-004 --> VANI-005 (engine)
   VANI-005 --+-- VANI-006 (TUI + transcript)   [also needs VANI-003]
              |-- VANI-007 (guardrail)
              |-- VANI-010 (pytest harness + replay)
```

**Parallelization hints:**

- After VANI-001, the three roots VANI-002, VANI-004, and VANI-009 can run in parallel.
- VANI-008 can run after VANI-003, in parallel with the engine track.
- After VANI-005, the leaves VANI-006, VANI-007, and VANI-010 can run in parallel (VANI-006 also needs VANI-003).

---

## Stage 1 — Foundation

### VANI-001 — Project scaffold and tooling

**Description:**
Stand up the `src/` Python project so every other issue has a place to live. This is the base of v0 P0.

**What needs to be done:**
- Create the repo's Python project: a `.venv` virtualenv and `pyproject.toml` (Python 3.11+, dependencies: `anthropic`, `textual`; dev extra `[dev]`: `pytest`, `pytest-asyncio`, `ruff`).
- Create the `src/` package with the module layout from architecture §2 (`app/`, `core/`, `planner/`, `llm/`, `state/`, `contracts/`, `engine.py`, `telemetry/`, `config/`, `tui/`, plus empty placeholders for later modules).
- Create `tests/` (unit + a `replay/` area for the headless harness, VANI-010).
- Configure `ruff` (lint + format) and `pytest` in `pyproject.toml`.
- Add `README`/`.env.example` and document setup: `python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`.

**Dependencies:** None

**Expected result:**
A clean, installable skeleton: the package imports, `ruff` and `pytest` run (no tests yet), and the module layout matches the architecture.

**Acceptance criteria:**
- [ ] `python -m venv .venv && pip install -e ".[dev]"` exits 0
- [ ] `import src` and all sub-packages import without error
- [ ] `ruff check .` and `pytest` both run (pytest reports 0 tests, exit 0)
- [ ] Directory layout matches the Solution Structure in `architecture-v0.1.en.md` §2

---

### VANI-002 — Repository interface and json_store

**Description:**
The single state-access point. Every layer reads/writes state through `Repository`; `json_store` backs it for all of Versions 0–1 (architecture §4, §10).

**What needs to be done:**
- Define the `Repository` interface in `state/repository.py`: load/save by document type and id, list, delete.
- Implement `state/json_store.py` (local JSON files, one area per document type).
- No personality layer may import a concrete store — only the interface.
- Add a hook point for at-rest encryption of sensitive documents (implemented later; refinement #1).

**Dependencies:** VANI-001

**Expected result:**
A working repository with a JSON backing store that round-trips documents and is the only state entry point.

**Acceptance criteria:**
- [ ] `Repository` exposes load/save/list/delete by document type
- [ ] `json_store` round-trips a document (save then load returns equal data, UTF-8 safe)
- [ ] Swapping the store implementation requires no change outside `state/`
- [ ] Unit tests cover save/load/list/delete

---

### VANI-003 — Data contracts and versioned schemas

**Description:**
The shared, serializable data contracts and the persisted-document schemas, defined once in `contracts/` and exported as JSON Schema (architecture §9).

**What needs to be done:**
- Create the `contracts/` module with serializable models (dataclasses/pydantic).
- Add a `schema_version` field to every persisted document and implement **migrate-on-read** in the repository.
- Keep `architecture/schemas/*.schema.json` in sync as the exported JSON Schema (one file per document/contract); add a test that each model validates against its schema.
- For P0, realize the `sessions` document shape (`architecture/schemas/sessions.schema.json`); other documents are realized in their own phases.

**Dependencies:** VANI-002

**Expected result:**
A single source of truth for data shapes; documents carry a version and migrate forward on read; models and JSON Schema agree.

**Acceptance criteria:**
- [ ] Every persisted document has `schema_version`
- [ ] Repository migrates an older `schema_version` to current on read
- [ ] Each contract model validates against its `architecture/schemas/*.schema.json`
- [ ] A schema-drift test fails if a model and its JSON Schema diverge

---

## Stage 2 — Brain & LLM

### VANI-004 — LLM client (Opus, streaming)

**Description:**
The `llm` module is the only place the model is called, which keeps it mockable in tests (architecture §11). P0 needs the Opus path with streaming; Haiku and the prompt-prefix cache arrive at v0 P1 / v1 P1.

**What needs to be done:**
- Implement an `llm` client over the Anthropic SDK with **streaming** output.
- Expose a small interface (e.g. `generate(messages, system) -> stream`) that returns text deltas and token-usage on completion.
- Read the API key from config/env (never hardcode).
- Make the client injectable/mockable (so VANI-010 can stub it).

**Dependencies:** VANI-001

**Expected result:**
A streaming Opus client behind a thin, mockable interface, returning text and usage.

**Acceptance criteria:**
- [ ] A prompt returns streamed text deltas
- [ ] Token usage is returned on completion
- [ ] The client is injectable and can be replaced by a stub in tests
- [ ] API key comes from config/env

---

### VANI-005 — Transport-agnostic engine

**Description:**
The brain entry point that makes the v2 API a wrapper, not a rewrite (architecture §10). In P0 it is a thin pass-through to the `llm`; the planner plugs in at v0 P1.

**What needs to be done:**
- Implement `engine.handle_turn(session_id, user_input) -> response` (async), plus an event/stream variant for streamed output.
- Load and persist all per-session state through the `Repository` keyed by `session_id` — no module-level/global state.
- The engine imports no transport code (no TUI, no server).
- For P0, the engine appends the user turn, calls the `llm`, and returns the streamed reply.

**Dependencies:** VANI-002, VANI-004

**Expected result:**
A single transport-agnostic entry point that any surface (TUI now, server later) drives, with session state externalized to the repository.

**Acceptance criteria:**
- [ ] `engine.handle_turn` runs a full turn and streams a reply
- [ ] All session state is read/written via the repository, keyed by `session_id`
- [ ] No import of `tui`/`server`/transport modules from `engine`/brain
- [ ] Two `session_id`s maintain independent state

---

## Stage 3 — Interface

### VANI-006 — TUI loop and transcript persistence

**Description:**
The text UI that drives the engine and persists conversation history as the `sessions` document.

**What needs to be done:**
- Build the Textual TUI: input field, scrollable transcript, status line.
- The TUI is a thin **adapter** over `engine.handle_turn` (architecture §10) — it holds no brain logic.
- Persist and reload transcript history via the repository (`sessions`; `architecture/schemas/sessions.schema.json`).
- Render streamed reply deltas as they arrive.

**Dependencies:** VANI-005, VANI-003

**Expected result:**
A usable text chat that streams replies and whose history survives a restart.

**Acceptance criteria:**
- [ ] User can hold a streaming text conversation
- [ ] Transcript scrolls; status line renders
- [ ] History is persisted to `sessions` and reloaded on restart
- [ ] The TUI calls only `engine.handle_turn` (no direct `llm`/state access)

---

## Stage 4 — Identity & Safety

### VANI-007 — Minimal guardrail pass (placeholder Guardian)

**Description:**
A minimal synchronous output check standing in for the full Guardian (which arrives at v1 P4). Safety is never deferred off the synchronous path (architecture §12, §13).

**What needs to be done:**
- Add a synchronous guardrail step between generation and display in the engine.
- Implement a minimal block/allow check (placeholder rules) with a clear extension point for the full Guardian.
- Log guardrail outcomes via telemetry (VANI-009).

**Dependencies:** VANI-005

**Expected result:**
Every reply passes a synchronous guardrail before being shown, with a seam for the real Guardian later.

**Acceptance criteria:**
- [ ] No reply reaches the TUI without passing the guardrail
- [ ] The guardrail can block/redirect output
- [ ] Outcome is recorded in telemetry
- [ ] The interface is ready for the full Guardian to drop in at v1 P4

---

### VANI-008 — Placeholder canon and confidence scaffolding

**Description:**
A minimal identity so the assistant is *someone* in P0, plus the cross-cutting confidence fields the later layers rely on.

**What needs to be done:**
- Author a minimal placeholder `canon` document (name + a short identity block) — full bible comes at v1 P1 (`architecture/schemas/canon.schema.json`).
- Compile the canon into a system prompt block passed to the `llm`.
- Scaffold a `confidence` (0–1) field on state elements that will carry it; the canon and hard invariants carry none.

**Dependencies:** VANI-003

**Expected result:**
A recognizable (if thin) identity in replies, and confidence fields present in state for later phases.

**Acceptance criteria:**
- [ ] A placeholder canon loads via the repository and shapes the system prompt
- [ ] Confidence fields exist on the relevant state elements
- [ ] The canon carries no confidence
- [ ] Replies reflect the placeholder identity

---

### VANI-009 — Logging and telemetry scaffolding

**Description:**
Structured logging and a telemetry sink (no metrics yet) so later phases (per-turn metrics at v0 P1) have somewhere to write.

**What needs to be done:**
- Implement structured logging with configurable levels in `telemetry/` (or `utils/`).
- Add a telemetry sink that later phases append per-turn records to (`architecture/schemas/telemetry.schema.json` shape; populated at v0 P1).
- Redact sensitive fields from telemetry (refinement #1).

**Dependencies:** VANI-001

**Expected result:**
Working structured logging and an empty-but-ready telemetry sink with redaction in place.

**Acceptance criteria:**
- [ ] Log level is configurable; logs are structured
- [ ] A telemetry record can be written and read back
- [ ] Sensitive fields are redacted in telemetry output
- [ ] No metrics are computed yet (scaffolding only)

---

## Stage 5 — Testing

### VANI-010 — pytest harness and headless replay

**Description:**
The test foundation for all of Version 0: `pytest` plus a headless replay harness that drives turns through the repository with a mocked `llm` (architecture §14; roadmap cross-cutting testing policy).

**What needs to be done:**
- Wire `pytest` (and `pytest-asyncio`) so `pytest` runs green.
- Build a **headless replay** path that calls `engine.handle_turn` with a stubbed `llm` and a temp repository, asserting on resulting state.
- Provide fixtures: a temp `json_store`, a fake/stub `llm`, and a sample session.
- Add the first unit tests for VANI-002, VANI-005, and the guardrail (VANI-007).

**Dependencies:** VANI-005

**Expected result:**
`pytest` is green and a headless replay can exercise a full turn without live API calls — the basis for per-phase tests and later ablations (refinement #3).

**Acceptance criteria:**
- [ ] `pytest` runs green in CI/local
- [ ] A headless replay drives a full turn with a mocked `llm` and temp repository
- [ ] Fixtures for temp store, stub llm, and a sample session exist
- [ ] Unit tests cover repository, engine, and guardrail
