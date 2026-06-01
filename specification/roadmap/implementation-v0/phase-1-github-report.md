# Version 0, Phase 1 — GitHub Issues Report

**Uploaded:** 2026-06-01
**Repository:** https://github.com/ichMaster/vani
**Source:** `specification/roadmap/implementation-v0/phase-1-issues.md`
**Total issues:** 8

## Issue Mapping

| VANI ID | GitHub # | Title | Labels | URL |
|---------|----------|-------|--------|-----|
| VANI-011 | #11 | Pipeline contracts: PerceptionResult and TurnPlan | p1::phase:1, p1::size:S, p1::stage:Contracts | https://github.com/ichMaster/vani/issues/11 |
| VANI-012 | #12 | Perception step (Haiku classification) | p1::phase:1, p1::size:M, p1::stage:Pipeline | https://github.com/ichMaster/vani/issues/12 |
| VANI-013 | #13 | Deterministic router (simple vs. deep) | p1::phase:1, p1::size:S, p1::stage:Pipeline | https://github.com/ichMaster/vani/issues/13 |
| VANI-014 | #14 | Dispatch and post-update hook | p1::phase:1, p1::size:M, p1::stage:Pipeline | https://github.com/ichMaster/vani/issues/14 |
| VANI-015 | #15 | LLM failure handling in dispatch | p1::phase:1, p1::size:S, p1::stage:Robustness-LLM | https://github.com/ichMaster/vani/issues/15 |
| VANI-016 | #16 | Prompt-prefix assembly in llm | p1::phase:1, p1::size:S, p1::stage:Robustness-LLM | https://github.com/ichMaster/vani/issues/16 |
| VANI-017 | #17 | Per-turn telemetry | p1::phase:1, p1::size:S, p1::stage:Observability | https://github.com/ichMaster/vani/issues/17 |
| VANI-018 | #18 | TUI token/cost calculator | p1::phase:1, p1::size:S, p1::stage:Observability | https://github.com/ichMaster/vani/issues/18 |

## Dependencies (added as issue comments)

| Issue | Blocked by |
|---|---|
| #11 VANI-011 | #3 (v0 P0) |
| #12 VANI-012 | #11, #4 (v0 P0) |
| #13 VANI-013 | #11 |
| #14 VANI-014 | #12, #13 |
| #15 VANI-015 | #14 |
| #16 VANI-016 | #4 (v0 P0) |
| #17 VANI-017 | #14, #9 (v0 P0) |
| #18 VANI-018 | #17, #6 (v0 P0) |

## Labels Created

- p1::phase:1
- p1::size:S, p1::size:M, p1::size:L
- p1::stage:Contracts, p1::stage:Pipeline, p1::stage:Robustness-LLM, p1::stage:Observability
