# Version 0, Phase 1 — Planner Skeleton and Tiers: GitHub Issues

Decomposes roadmap `v0 P1` into implementable issues. IDs continue Version 0 numbering (`VANI-011`…). Labels follow the `upload-issues` skill: `p1::phase:1`, `p1::size:*`, `p1::stage:*`.

**Phase prerequisite:** v0 P0 complete (VANI-001–010) — in particular the engine (VANI-005), the `llm` client (VANI-004), the repository/contracts (VANI-002, VANI-003), the TUI (VANI-006), and telemetry scaffolding (VANI-009).

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | VANI-011 | Pipeline contracts: PerceptionResult and TurnPlan | S | 1 — Contracts | VANI-003 (v0 P0) |
| 2 | VANI-012 | Perception step (Haiku classification) | M | 2 — Pipeline | VANI-011, VANI-004 (v0 P0) |
| 3 | VANI-013 | Deterministic router (simple vs. deep) | S | 2 — Pipeline | VANI-011 |
| 4 | VANI-014 | Dispatch and post-update hook | M | 2 — Pipeline | VANI-012, VANI-013 |
| 5 | VANI-015 | LLM failure handling in dispatch | S | 3 — Robustness & LLM | VANI-014 |
| 6 | VANI-016 | Prompt-prefix assembly in llm | S | 3 — Robustness & LLM | VANI-004 (v0 P0) |
| 7 | VANI-017 | Per-turn telemetry | S | 4 — Observability | VANI-014, VANI-009 (v0 P0) |
| 8 | VANI-018 | TUI token/cost calculator | S | 4 — Observability | VANI-017, VANI-006 (v0 P0) |

**Size legend:** S = 1–2 days, M = 3–5 days, L = 5–8 days

---

## Dependency Tree

```
VANI-011 (contracts) --+-- VANI-012 (perception)  <- VANI-004 (v0 P0)
                       |-- VANI-013 (router)
                              \
   VANI-012 + VANI-013 --------> VANI-014 (dispatch + post-update)
                                    |-- VANI-015 (failure handling)
                                    |-- VANI-017 (telemetry) <- VANI-009 (v0 P0)
                                              \
                                               VANI-018 (TUI token meter) <- VANI-006 (v0 P0)

VANI-016 (prompt-prefix assembly) <- VANI-004 (v0 P0)   [independent track]
```

**Parallelization hints:**

- VANI-013 and VANI-012 can run in parallel after VANI-011.
- VANI-016 is independent and can run any time after v0 P0.
- VANI-015, VANI-017 run after VANI-014; VANI-018 runs after VANI-017.

---

## Stage 1 — Contracts

### VANI-011 — Pipeline contracts: PerceptionResult and TurnPlan

**Description:**
The two in-memory contracts that flow through the per-turn pipeline (architecture §9). Defining them first lets perception, routing, and dispatch be built and tested against fixed shapes.

**What needs to be done:**
- Add `PerceptionResult` and `TurnPlan` to `contracts/` (serializable; architecture §9).
- `PerceptionResult`: topic, intent, emotion, modality, style signals — each with confidence (`architecture/schemas/perception_result.schema.json`). For P1, only topic + intent are populated (emotion/modality arrive at v0 P3); keep the fields present.
- `TurnPlan`: route (simple/deep), strategy, facet weights, target length, filler, confirmation, conversation-line action (`architecture/schemas/turn_plan.schema.json`). For P1, populate route + a minimal plan; richer fields fill in later phases.
- Keep both in sync with their JSON Schema (schema-drift test from VANI-003).

**Dependencies:** VANI-003 (v0 P0)

**Expected result:**
Two validated, serializable contracts the rest of the pipeline depends on.

**Acceptance criteria:**
- [ ] `PerceptionResult` and `TurnPlan` exist in `contracts/` and serialize round-trip
- [ ] Each validates against its `architecture/schemas/*.schema.json`
- [ ] Confidence fields are present on the inferred `PerceptionResult` fields
- [ ] Schema-drift test passes

---

## Stage 2 — Pipeline

### VANI-012 — Perception step (Haiku classification)

**Description:**
The only LLM call at the input: a single Haiku call that reads the message and returns a structured `PerceptionResult` (spec §9.2 step 1). It does not reply to the user.

**What needs to be done:**
- Implement the perception call in `planner/` using the `llm` client's Haiku tier (already supported via `tier="haiku"` since v0 P0).
- Return structured JSON parsed into `PerceptionResult`: topic, intent (emotion/modality added at v0 P3).
- Attach a confidence to each field.
- Make the call mockable for the headless replay harness.

**Dependencies:** VANI-011, VANI-004 (v0 P0)

**Expected result:**
A structured perception result produced by one Haiku call per turn.

**Acceptance criteria:**
- [ ] One Haiku call returns a valid `PerceptionResult` (topic, intent, confidences)
- [ ] Malformed model output is handled (re-ask/fallback, not a crash)
- [ ] The call is mockable in tests
- [ ] Telemetry records the perception latency/tokens (via VANI-017)

---

### VANI-013 — Deterministic router (simple vs. deep)

**Description:**
Scored code (no LLM) that decides simple → Haiku vs. deep → Opus from the `PerceptionResult` (spec §9.5).

**What needs to be done:**
- Implement a deterministic router in `planner/` producing the `route` field of `TurnPlan`.
- Use thresholds/signals: simple facts, confirmations, short chit-chat stay simple; emotional weight, ambiguity, high stakes, multi-facetedness escalate to deep.
- Expose thresholds as config knobs (`config/`).

**Dependencies:** VANI-011

**Expected result:**
A transparent, tunable routing decision recorded in the turn plan.

**Acceptance criteria:**
- [ ] Router maps representative inputs to the expected route
- [ ] Thresholds are config-driven, not hardcoded
- [ ] Route is written to `TurnPlan`
- [ ] Unit tests cover simple and deep cases

---

### VANI-014 — Dispatch and post-update hook

**Description:**
Execute the routed turn (Haiku directly, or one Opus call), then run the deterministic post-update that feeds state back for the next turn (spec §9.2 steps 4–5).

**What needs to be done:**
- Insert perception + routing into the existing gated turn loop (`engine.handle_turn` already buffers the reply, gates it through the Guardian, and persists the turn since v0 P0).
- Branch dispatch on the route: simple → Haiku generates; deep → one Opus call.
- Keep the synchronous guardrail before display (already in place from VANI-007, v0 P0).
- Extend the post-update hook to record the route / turn plan alongside the persisted turn.
- Confirm a deep turn makes exactly two LLM calls (one Haiku perception + one Opus generation).

**Dependencies:** VANI-012, VANI-013

**Expected result:**
A full structured turn end to end: perception → route → dispatch → guardrail → post-update.

**Acceptance criteria:**
- [ ] Simple turn = one Haiku call; deep turn = one Haiku + one Opus call
- [ ] Candidate passes the guardrail before reaching the TUI
- [ ] Post-update persists the turn through the repository
- [ ] Headless replay exercises both routes

---

## Stage 3 — Robustness & LLM

### VANI-015 — LLM failure handling in dispatch

**Description:**
Graceful degradation so the turn never crashes (architecture §12; spec §15).

**What needs to be done:**
- On timeout/slow Opus: emit a short "give me a moment" filler, then retry with backoff.
- On connectivity loss: return an honest message (the local-LLM offline fallback is a later robustness pass).
- Ensure a failed turn leaves state consistent (no half-written turn).

**Dependencies:** VANI-014

**Expected result:**
Dispatch survives LLM timeouts and connectivity loss without crashing or corrupting state.

**Acceptance criteria:**
- [ ] Simulated timeout → filler + retry with backoff
- [ ] Simulated connectivity loss → honest message, no crash
- [ ] State remains consistent after a failed turn
- [ ] Failure paths covered by tests (mocked llm errors)

---

### VANI-016 — Prompt-prefix assembly in llm

**Description:**
Assemble the prompt as a cached prefix + fresh suffix so caching and cost control work from early on (architecture §11). The full canon/temperament caching arrives at v1; P1 lays the structure with a placeholder system block.

**What needs to be done:**
- In `llm/`, assemble prompts as: cached prefix (system/identity block — the placeholder canon from VANI-008) + fresh suffix (turn plan context + recent transcript).
- Wire Anthropic prompt caching on the prefix (cache the system block).
- Keep the seam for the daily-temperament block (added at v1 P2).

**Dependencies:** VANI-004 (v0 P0)

**Expected result:**
A prefix/suffix prompt structure with the system block cached, ready for the full canon later.

**Acceptance criteria:**
- [ ] Prompts are assembled as cached prefix + fresh suffix
- [ ] The system block is sent with prompt caching enabled
- [ ] Cache reads are visible in token usage/telemetry
- [ ] Structure leaves a clear slot for the temperament block (v1 P2)

---

## Stage 4 — Observability

### VANI-017 — Per-turn telemetry

**Description:**
Emit a telemetry record per turn into the sink scaffolded at VANI-009 (spec §20; `architecture/schemas/telemetry.schema.json`).

**What needs to be done:**
- After each turn, write a telemetry record: route taken, latencies (perception, generation, time-to-first-token), and token usage (Haiku vs. Opus input/output, cache reads).
- Conform to `architecture/schemas/telemetry.schema.json`.
- Redact sensitive fields (refinement #1).

**Dependencies:** VANI-014, VANI-009 (v0 P0)

**Expected result:**
Every turn produces a structured, schema-conformant telemetry record.

**Acceptance criteria:**
- [ ] Each turn writes a record matching `telemetry.schema.json`
- [ ] Route, latencies, and per-tier token usage are captured
- [ ] Cache reads are recorded
- [ ] Sensitive fields are redacted

---

### VANI-018 — TUI token/cost calculator

**Description:**
Surface token usage and estimated cost in the TUI status line, derived from telemetry (roadmap v0 P1).

**What needs to be done:**
- Add a token/cost meter to the TUI status line: per-turn and cumulative token counts (Haiku vs. Opus, cache reads) and an estimated cost.
- Source the numbers from the telemetry records (VANI-017) — the TUI does not call the `llm` directly.
- Make per-tier prices config-driven (`config/`) so cost estimates can be updated.

**Dependencies:** VANI-017, VANI-006 (v0 P0)

**Expected result:**
A live token/cost readout in the TUI for each turn and the session total.

**Acceptance criteria:**
- [ ] Status line shows per-turn token counts (Haiku/Opus/cache) and cost
- [ ] Status line shows cumulative session tokens and cost
- [ ] Numbers come from telemetry, not a direct llm call
- [ ] Per-tier prices are config-driven
