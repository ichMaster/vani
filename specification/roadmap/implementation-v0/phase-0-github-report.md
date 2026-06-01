# Version 0, Phase 0 — GitHub Issues Report

**Uploaded:** 2026-06-01
**Repository:** https://github.com/ichMaster/vani
**Source:** `specification/roadmap/implementation-v0/phase-0-issues.md`
**Total issues:** 10

## Issue Mapping

| VANI ID | GitHub # | Title | Labels | URL |
|---------|----------|-------|--------|-----|
| VANI-001 | #1 | Project scaffold and tooling | p0::phase:0, p0::size:S, p0::stage:Foundation | https://github.com/ichMaster/vani/issues/1 |
| VANI-002 | #2 | Repository interface and json_store | p0::phase:0, p0::size:S, p0::stage:Foundation | https://github.com/ichMaster/vani/issues/2 |
| VANI-003 | #3 | Data contracts and versioned schemas | p0::phase:0, p0::size:M, p0::stage:Foundation | https://github.com/ichMaster/vani/issues/3 |
| VANI-004 | #4 | LLM client (Opus, streaming) | p0::phase:0, p0::size:S, p0::stage:Brain-LLM | https://github.com/ichMaster/vani/issues/4 |
| VANI-005 | #5 | Transport-agnostic engine | p0::phase:0, p0::size:M, p0::stage:Brain-LLM | https://github.com/ichMaster/vani/issues/5 |
| VANI-006 | #6 | TUI loop and transcript persistence | p0::phase:0, p0::size:M, p0::stage:Interface | https://github.com/ichMaster/vani/issues/6 |
| VANI-007 | #7 | Minimal guardrail pass (placeholder Guardian) | p0::phase:0, p0::size:S, p0::stage:Identity-Safety | https://github.com/ichMaster/vani/issues/7 |
| VANI-008 | #8 | Placeholder canon and confidence scaffolding | p0::phase:0, p0::size:S, p0::stage:Identity-Safety | https://github.com/ichMaster/vani/issues/8 |
| VANI-009 | #9 | Logging and telemetry scaffolding | p0::phase:0, p0::size:S, p0::stage:Identity-Safety | https://github.com/ichMaster/vani/issues/9 |
| VANI-010 | #10 | pytest harness and headless replay | p0::phase:0, p0::size:M, p0::stage:Testing | https://github.com/ichMaster/vani/issues/10 |

## Dependencies (added as issue comments)

| Issue | Blocked by |
|---|---|
| #2 VANI-002 | #1 |
| #3 VANI-003 | #2 |
| #4 VANI-004 | #1 |
| #5 VANI-005 | #2, #4 |
| #6 VANI-006 | #5, #3 |
| #7 VANI-007 | #5 |
| #8 VANI-008 | #3 |
| #9 VANI-009 | #1 |
| #10 VANI-010 | #5 |

(#1 VANI-001 has no dependencies.)

## Labels Created

- p0::phase:0
- p0::size:S, p0::size:M, p0::size:L
- p0::stage:Foundation, p0::stage:Brain-LLM, p0::stage:Interface, p0::stage:Identity-Safety, p0::stage:Testing
