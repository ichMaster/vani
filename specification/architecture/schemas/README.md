# Data Schemas

JSON Schema (draft 2020-12) for Vani's data contracts. These are the authoritative shapes referenced by architecture §9 (Data Contracts and Schemas) and specification §13 (State Model). Both `json_store` and `mongo_store` serialize the same schemas; the runtime models in `src/contracts/` are the source of truth and these files are their export.

## Conventions

- **`schema_version`** — every persisted document carries it; the repository migrates on read (old → current), so field evolution and the JSON → Mongo move (v3 P2) never break existing state.
- **Confidence** — most inferred state carries a `confidence` (number, 0–1) that rises with confirmation and decays over time. The **canon and the hard invariants carry no confidence** — they are a stable foundation, not hypotheses.
- **Sensitivity** — the user's birth data and the portrait's interpretive hypotheses are sensitive: encrypted at rest in the repository, redacted in telemetry, deletable on demand (architecture §13).
- Schemas are intentionally lenient (extra properties allowed) at this early stage; tighten as the contracts stabilize.

## Persisted documents (architecture §4)

| File | Document | Confidence | Notes |
|---|---|:--:|---|
| `canon.schema.json` | `canon` | no | stable character bible + hard invariants |
| `users.schema.json` | `users` | partial | profile, birth data (sensitive), synastry |
| `portrait.schema.json` | `portrait` | yes | observational + interpretive layers, style profile |
| `conversation_line.schema.json` | `conversation_line` | yes | open loops, arc goals/phase, initiative budget |
| `question_bank.schema.json` | `question_bank` | — | curiosity questions with sensitivity + aging |
| `material.schema.json` | `material` | no | raw observations, pre-interpretation |
| `sessions.schema.json` | `sessions` | — | per-session turn history |
| `telemetry.schema.json` | `telemetry` | — | per-turn metrics |
| `validation_log.schema.json` | `validation_log` | — | code-vs-model discrepancies for tuning |

## In-memory pipeline contracts (architecture §9)

| File | Contract | Produced by |
|---|---|---|
| `perception_result.schema.json` | `PerceptionResult` | the perception step (Haiku) |
| `turn_plan.schema.json` | `TurnPlan` | the decision step (deterministic code) |
