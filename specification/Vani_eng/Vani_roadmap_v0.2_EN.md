# Vani — Implementation Roadmap

Living-personality voice companion. Backend — Python. Version 0.3 (reprioritized by review scores).
The "when" document. The "what" is in the specification (v1.8). The "how" is in the architecture (v0.1).

---

## 1. Principle

The phase order is reprioritized by the consolidated review scores: **concepts scoring >= 8 are built first** — the planner (8), the conversation line (10), the portrait with cross-cutting confidence (13 and 8), and the background pass (9) — so that the most valuable cognitive machinery runs and is validated earliest. **The rest then follows the existing plan:** canon, astro and temperament, onboarding, weighted facets with the Guardian, delivery, memory. As before, the whole brain lives first in a text TUI, then voice (P11), then server and MongoDB (P12), then the device (P13); state is JSON through P11 and Mongo from P12, behind the same repository.

```mermaid
flowchart LR
  P0["P0 skeleton"] --> P1["P1 planner (8)"] --> P2["P2 line (10)"] --> P3["P3 portrait (13) + confidence (8)"] --> P4["P4 background (9)"] --> M{{"High-score concepts in text"}}
  M --> P5["P5 canon"] --> P6["P6 astro + temperament"] --> P7["P7 onboarding"] --> P8["P8 facets + Guardian"] --> P9["P9 delivery"] --> P10["P10 memory"] --> M2{{"All layers in text"}}
  M2 --> P11["P11 voice"] --> P12["P12 server + Mongo"] --> P13["P13 device"]
```

**Reprioritization trade-off:** the early personality is thin in character and flat in delivery (a minimal placeholder canon and plain-text delivery), because canon, facets, onboarding, and mirroring are filled in during the second wave; safety is held by the minimal gate from P0 until the full Guardian arrives at P8.

Each phase is described by: goal; scope (what is added); modules; state; dependencies; tasks; definition of done.

---

## 2. Phases

## Wave 1 — concepts scoring >= 8

### Phase 0 — Chat Skeleton (TUI)
- **Goal:** a working text chat with the model.
- **Scope:** the TUI loop, an Opus call, a response; a minimal safety check; the repository interface from day one; a minimal placeholder canon (identity) and confidence scaffolding in state.
- **Modules:** tui, llm, state.
- **State:** a JSON snapshot of history; confidence scaffolding.
- **Dependencies:** none.
- **Tasks:**
  - Scaffold the Python project, packaging, dependency management, linting.
  - Define the `Repository` interface and a first `json_store` implementation (load/save by document type).
  - Implement the `llm` client over the Anthropic SDK (Opus), with streaming.
  - Build the TUI loop (input field, scrollable transcript, status line).
  - Persist and reload transcript history via the repository.
  - Add a minimal guardrail pass on output (placeholder for the Guardian).
  - Author a minimal placeholder canon so the assistant has an identity.
  - Scaffold confidence fields on state elements.
  - Set up logging/telemetry scaffolding (no metrics yet).
- **Definition of done:** the user can hold a streaming text conversation; history survives restart.

### Phase 1 — Planner Skeleton and Tiers (score 8)
- **Goal:** a structured turn pipeline.
- **Scope:** perception (a Haiku classification), deterministic routing (simple -> Haiku, complex -> Opus), dispatch, a minimal turn plan.
- **Modules:** planner; telemetry (start).
- **State:** turn plan, telemetry.
- **Dependencies:** P0.
- **Tasks:**
  - Define the `TurnPlan` data structure.
  - Implement the perception call on Haiku returning structured JSON (topic, intent; emotion/modality added later).
  - Implement the deterministic router (simple vs. deep) with thresholds.
  - Implement dispatch for both routes and a post-update hook.
  - Emit per-turn telemetry (route taken, latencies, token usage).
  - Add prompt-prefix assembly in `llm` (system block placeholder).
- **Definition of done:** classification and routing are observable; two LLM calls on a deep turn.

### Phase 2 — Conversation Line (score 10)
- **Goal:** a led conversation rather than a reaction.
- **Scope:** open loops, arc goals, phases, follow-ups (including cross-session), the initiative budget.
- **Modules:** line, state (persistence).
- **State:** conversation_line.
- **Dependencies:** P1. Delivery is a plain-text stub for now; full mirroring at P9.
- **Tasks:**
  - Define the open-loop record and its lifecycle (open/deferred/closed) with significance weight and intent owner.
  - Implement arc-goal stack and arc-phase tracking (opening -> ... -> closing).
  - Implement the follow-up queue, including cross-session surfacing.
  - Implement the initiative budget (decrement on lead, refill on user-led turns).
  - Wire conversation-line actions into the decision step (pick up loop, follow-up, converge).
  - Add the accuracy safeguard for callbacks.
- **Definition of done:** the assistant returns to deferred threads, poses follow-ups, and converges in the closing phase.

### Phase 3 — Portrait, Confidence, Modality (scores 13 and 8)
- **Goal:** a model of the user; decisions account for confidence; reading of jokes.
- **Scope:** the two-layer portrait and the material box; confidence as a cross-cutting attribute; the modality filter in perception.
- **Modules:** portrait, planner extension.
- **State:** portrait, material; confidence on state elements.
- **Dependencies:** P1, P2, and the minimal canon (P0). Facet lenses are realized in the interpretation prompt for now; runtime weighted facets replace them at P8.
- **Tasks:**
  - Implement the observational layer (the material box appended each turn).
  - Define the interpretive layer (hypotheses about the user's facets with confidence).
  - Add confidence to every relevant state element; implement rise and time-decay.
  - Wire confidence into planner decisions (ask again / cautious strategy / mirror less).
  - Extend perception with the utterance-modality field (joke/serious/hypothetical/sarcasm/quotation, with confidence).
  - Apply modality effects to tone and to what enters the portrait; keep the safety safeguard.
- **Definition of done:** the portrait builds; uncertainty changes behavior; sarcasm and jokes are not taken literally.

### Phase 4 — Background Pass (Async) (score 9)
- **Goal:** self-correction and curiosity.
- **Scope:** the async pass — policy validation + portrait growth + question generation into the bank; the curiosity cycle.
- **Modules:** background.
- **State:** question_bank, validation_log, updates to portrait and line.
- **Dependencies:** P3.
- **Tasks:**
  - Implement the asyncio background task and the material queue.
  - Implement policy validation (facets/strategy/classification/missed loops) with shadow and active modes.
  - Implement portrait growth from accumulated material.
  - Implement question generation into the bank (hypothesis link, sensitivity, appropriateness condition, aging).
  - Implement curiosity as a loop class; add question selection at curiosity moments (relevance + sensitivity + budget).
  - Apply background conclusions to state softly, with inertia; keep the Guardian synchronous and outside.
  - Add selective triggering (uncertainty threshold, sampling, pauses).
- **Definition of done:** the system self-corrects and asks curiosity-driven questions without blocking the response.

**Milestone: the high-score concepts (score >= 8) work in text.**

## Wave 2 — the rest, in the existing plan order

### Phase 5 — Layer 1: Character Core (Canon)
- **Goal:** a stable character.
- **Scope:** a hand-authored character bible compiled into a cached identity block; the invariants (expands the P0 placeholder canon into the full bible).
- **Modules:** core.
- **State:** canon.
- **Dependencies:** P1.
- **Tasks:**
  - Define the canon schema (all Layer 1 dimensions).
  - Author the full character bible (replacing the P0 placeholder).
  - Compile the canon into a cached system-prompt prefix; wire prompt caching in `llm`.
  - Encode the hard invariants as a non-overridable prompt section.
  - Add a canon-loading path through the repository.
- **Definition of done:** the assistant shows a recognizable personality in text; the identity block is cached.

### Phase 6 — Astro Engine and Layer 2 (Temperament)
- **Goal:** a daily mood.
- **Scope:** natal (a fixed date for now) and transits via skyfield; the temperament dials in the prompt.
- **Modules:** astro.
- **State:** astro state (natal, daily transits).
- **Dependencies:** P5.
- **Tasks:**
  - Integrate skyfield; cache the ephemeris locally.
  - Compute the natal chart from a configured date.
  - Compute daily transits to the natal chart.
  - Map astro state to the five dials (energy, warmth, verbosity, imagination, caution).
  - Render a cached daily temperament block into the prompt; refresh once per day.
  - Verify the dials shift tone and verbosity in text.
- **Definition of done:** tone and verbosity vary by day; prosodic fluctuation deferred to Phase 11.

### Phase 7 — Onboarding (Birth)
- **Goal:** the character is born to fit the user.
- **Scope:** candidate-date search by synastry (the user's birth date) and purpose; previews; selection; the canon seed.
- **Modules:** astro (scoring), onboarding flow in tui.
- **State:** users (birth date, synastry), updated canon.
- **Dependencies:** P6.
- **Tasks:**
  - Add a TUI onboarding flow collecting the user's birth data, purpose, and assistant gender/name/age.
  - Map purpose to a target archetype and a desired chart signature.
  - Implement synastry computation (assistant chart x user chart).
  - Implement the scoring function (synastry-to-user + archetype fit), purpose-shaped.
  - Search candidate dates within the birth-year range; rank and pick 3-4 diverse candidates.
  - Generate a short character preview per candidate.
  - On selection, fix the natal chart and seed the canon (archetype, base temperament, wound-gift themes).
- **Definition of done:** instead of a fixed date, the natal chart is chosen at onboarding and seeds the canon.

### Phase 8 — Layer 3: Weighted Facets and the Guardian
- **Goal:** responses reflect weighted facets; an active safety gate.
- **Scope:** facet definitions, the weight formula, one weighted Opus call; the Guardian as a separate synchronous check. Replaces the interim lens-in-prompt from P3 with runtime weighted facets; activates the full Guardian (the minimal gate held since P0).
- **Modules:** facets, guardian.
- **State:** facet weights in the turn plan.
- **Dependencies:** P5, P6.
- **Tasks:**
  - Define the facet set and per-facet metadata (competency, goal, mode, archetype affinity).
  - Implement the weight formula (base affinity + topic relevance + temperament shift), clamped, with a threshold and max-active knob.
  - Assemble the weighted-facets emphasis in the Opus prompt (single call).
  - Mark internal-only facets as content modifiers, never the voice.
  - Implement the Guardian as a separate synchronous gate (block/redirect on safety/wellbeing).
  - Add facet weights and Guardian outcomes to telemetry.
- **Definition of done:** different facets come forward by topic and mood; everything spoken passes the Guardian.

### Phase 9 — Layer 4: Delivery
- **Goal:** style mirroring and a daily textual drift.
- **Scope:** the style profile (moving average), the envelope, fluctuation of position-in-envelope and lexical color. Replaces the plain-text delivery stub from P2.
- **Modules:** delivery.
- **State:** style profile.
- **Dependencies:** P1, P6.
- **Tasks:**
  - Implement the style profile (EMA of length, register, complexity, question density, language mix, impatience).
  - Derive the delivery envelope (target length, register) with partial convergence and a clarity floor.
  - Implement textual fluctuation: position within the envelope and lexical color from the dials.
  - Add the "never mirror the harmful" and "informal address only after the user" rules.
  - Enforce precedence (user envelope > fluctuation) when assembling the plan.
- **Definition of done:** terse to the user -> terse back; manner drifts by day; clarity floor never breached.

### Phase 10 — Memory and Persistence
- **Goal:** continuity across sessions.
- **Scope:** separation of session-scoped and long-term; consolidation of the local JSON store behind the repository.
- **Modules:** state.
- **State:** all documents with lifecycle policy.
- **Dependencies:** P2, P3, P4.
- **Tasks:**
  - Define lifecycle/retention policy per document (session vs. long-term).
  - Consolidate the JSON store; ensure atomic snapshot writes.
  - Implement merge of long-term baseline with session state on startup.
  - Handle privacy for the user's birth data (local, not exported).
  - Add migration-readiness checks for the eventual Mongo swap.
- **Definition of done:** character and portrait survive restarts. **Milestone: all layers in text.**

### Phase 11 — Voice: ASR + TTS
- **Goal:** a voice conversation on the developer's machine.
- **Scope:** Whisper (ASR) in, Piper-Ukrainian (TTS) out; prosodic fluctuation now active; barge-in.
- **Modules:** io (asr, tts), delivery extension.
- **State:** unchanged.
- **Dependencies:** all layers (P10).
- **Tasks:**
  - Integrate local Whisper (faster-whisper); expose transcript + optional prosody signals.
  - Integrate Piper-Ukrainian; expose synthesis parameters (rate, variation).
  - Map delivery fluctuation to prosody parameters from the dials.
  - Implement microphone capture, VAD, and speaker playback.
  - Implement barge-in (interrupt TTS, cancel in-flight Opus).
  - Verify Ukrainian quality by ear (especially stress); tune.
- **Definition of done:** you can speak with the assistant by voice; no server or device yet.

### Phase 12 — Server and MongoDB
- **Goal:** a backend for sessions and groundwork for the device.
- **Scope:** a FastAPI + WebSocket server around the brain; the protocol; the filler for latency hiding; MongoDB as the repository implementation in place of JSON.
- **Modules:** server, state (mongo_store).
- **State:** migration JSON -> Mongo behind the same interface.
- **Dependencies:** P11.
- **Tasks:**
  - Implement `mongo_store` against the existing `Repository` interface.
  - Migrate existing JSON state into Mongo collections.
  - Build the FastAPI + WebSocket server; wrap the brain; manage sessions.
  - Define the device-facing protocol (handshake, Opus audio frames).
  - Implement the filler path to hide Opus TTFT on deep turns.
  - Support multiple concurrent sessions over the same brain.
  - Add auth/session security and connection lifecycle handling.
- **Definition of done:** the brain is reachable over WebSocket; state is in Mongo; the filler hides Opus TTFT.

### Phase 13 — Hardware: Echo Pyramid
- **Goal:** a physical voice terminal.
- **Scope:** AtomS3R with xiaozhi firmware pointed at our server; bidirectional Opus audio streaming.
- **Modules:** device.
- **State:** unchanged.
- **Dependencies:** P12.
- **Tasks:**
  - Flash xiaozhi firmware to AtomS3R + Echo Pyramid via M5Burner.
  - Point the device at our server's WebSocket/OTA endpoint.
  - Verify Opus streaming both ways and wake-word behavior.
  - Tune end-to-end latency (filler timing, audio buffering).
  - Validate the full conversation loop on hardware.
- **Definition of done:** conversation through the Echo Pyramid; the complete target system.

---

## 3. Review-Driven Refinements (High Priority)

The six high-priority improvements from the reviews, mapped to phases. Full implementation notes are in `vani_high_priority_improvements_uk.md`.

| # | Improvement | Target phases | How (in brief) |
|---|---|:--:|---|
| 1 | Protect sensitive data | P0, P10 | Encrypt sensitive documents in `json_store` behind the `Repository` interface; redact in telemetry; delete on demand |
| 2 | Route facts to self-check | P1 | A `self_check` flag from perception; a conditional cheap verification call in dispatch |
| 3 | Ablations and metrics | after P4 | `config.ablation` flags; headless replay through `repository`; coherence/loop/contradiction metrics into telemetry (Haiku judge) |
| 4 | Red-team the Influence-Strategist | P8 | A "no manipulation in output" rule in the Guardian rubric; adversarial dialogues in the eval harness (from #3) |
| 5 | Formalize weights and confidence | P3, P4, P8 | Decay/reinforcement equations for confidence (`state/confidence.py`); explicit weight formula with tie-break; strategy utility learning |
| 6 | Operationalize anti-dependency | after P4, finalized P8 | A risk indicator from telemetry; reduced initiative budget and question frequency; offline check-ins |

Recommended order: quick wins first (1 data protection, 2 fact self-check), then 3 ablations as the basis for 4 red-teaming, then 5 formalization and 6 anti-dependency (best after P4, finalized with the full Guardian at P8).

---

## 4. Cross-Cutting Elements

Not separate phases; they accompany all: confidence and the Guardian are designed into the state scaffolding from early phases (a minimal safety check from P0, the full Guardian from P8); telemetry from P1; the state repository from P0 (so Phase 12 changes only the implementation).

---

## 5. Open Decisions

- TUI library: Textual or a simpler start.
- Whether to raise the minimal canon (P0) and basic delivery earlier if the early thinness of character hinders testing.
- Onboarding (P7) early, or temporarily live with a fixed date.
- Local ASR/TTS on the machine vs. cloud during P11.
- Background-pass cadence: shared between validation and portrait growth, or separated.
