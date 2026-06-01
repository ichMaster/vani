---
name: execute-issues
description: Execute GitHub issues for a phase sequentially - implement, validate, commit, push, and generate a report.
---

# Skill: Execute GitHub Issues

Execute GitHub issues for a phase sequentially: implement, validate, commit, push, and generate a report.

## Usage

```
/execute-issues <label> [--issue VANI-xxx] [--dry-run]
```

The `<label>` is the GitHub phase label exactly as it appears (e.g., `p1::phase:1`).

- `/execute-issues p1::phase:1` -- execute all issues labeled `p1::phase:1`
- `/execute-issues p1::phase:1 --issue VANI-003` -- execute a single issue from that phase
- `/execute-issues p1::phase:1 --dry-run` -- show execution plan without making changes

## Instructions

### Step 0: Verify prerequisites

1. Confirm we are on the expected branch (e.g., `main` or the user's working branch)
2. Confirm working tree is clean (`git status`)
3. Confirm `gh` is authenticated
4. Parse the label to determine phase:
   - Label `p1::phase:1` -> phase `y=1`
5. Fetch issues from GitHub:
   ```bash
   gh issue list --label "{label}" --state open --limit 100
   ```
6. Read the phase issues file for detailed descriptions: `specification/phase{y}-*.md`
7. If a GitHub report exists (`phase{y}-github-report.md`), read the VANI-to-GitHub# mapping

### Step 1: Build execution queue

From the GitHub issue list, build an ordered queue based on dependencies:
- Parse VANI-xxx IDs from issue titles (format: `VANI-xxx: {title}`)
- Determine dependency order from the phase issues file dependency tree
- Issues with no unmet dependencies go first
- Skip issues already closed on GitHub
- If `--issue VANI-xxx` is specified, execute only that issue (but verify its dependencies are closed)

Show the user the execution plan and ask for confirmation.

### Step 2: Execute each issue (loop)

For each issue in the queue:

#### 2a. Assign and announce

Print: `--- Starting VANI-xxx: {title} ---`

#### 2b. Read issue details

Read the full issue description from the phase issues file (the detailed section for this VANI-xxx).

#### 2c. Implement

Execute the tasks described in the issue. Follow the project conventions in `CLAUDE.md` and the design documents under `specification/`. Key rules:

- **Source layout:** implement under the `src/` package, placing code in the module that owns the concern per the architecture doc (`core/`, `astro/`, `planner/`, `facets/`, `delivery/`, `line/`, `portrait/`, `background/`, `guardian/`, `llm/`, `state/`, `io/`, `server/`, `device/`, `telemetry/`, `config/`, `tui/`).
- **Spec is authoritative:** the master specification (v1.8) defines the "what", the architecture doc the "how", the roadmap the "when". When behavior is unclear, defer to the spec rather than improvising; if the spec is silent, ask the user.
- **State behind the repository:** all state access goes through the `state/repository.py` interface. No personality layer may know whether JSON or Mongo sits beneath it.
- **The Guardian is synchronous; the background pass is not.** Never move a safety check off the synchronous path. The async background pass affects subsequent turns only.
- **Confidence is cross-cutting** on state elements (except the canon and hard invariants). Honor rise/decay where the issue touches state.
- Follow existing code style and patterns; keep imports and module boundaries clean.

#### 2d. Validate

Run validation checks:

1. **Syntax check:** `python3 -m py_compile {changed_py_files}` for each new/modified .py file
2. **Import check:** `python3 -c "import {module}"` for changed modules
3. **Tests:** run the test suite if one exists (e.g., `pytest`); run focused tests for the changed module when possible
4. **Lint/format:** run the project's configured linter/formatter if present (e.g., `ruff`, `black --check`)
5. **Spec consistency:** verify the change matches the relevant section of the spec/architecture docs
6. **Acceptance criteria:** go through each criterion from the issue and verify

Record pass/fail for each check.

Note: if a tool (tests, linter) is not yet configured in the project, note that the check was skipped rather than reporting a false pass.

#### 2e. Commit

```bash
git add {specific files created/modified}
git commit -m "$(cat <<'EOF'
VANI-xxx: {title}

{1-2 sentence summary of what was implemented}

Closes #{github-issue-number}

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

#### 2f. Push

```bash
git push
```

#### 2g. Close issue with summary

```bash
gh issue close {issue-number} --comment "$(cat <<'EOF'
## Implementation Summary

**Commit:** {commit-hash}
**Files changed:** {count}

### What was done
{bullet list of key changes}

### Validation
{pass/fail status for each check}

### Acceptance criteria
{checklist with pass/fail}
EOF
)"
```

#### 2h. Log progress

Append to the in-memory execution log:
- Issue ID, title
- Commit hash
- Files changed (list)
- Validation results
- Status: success/partial/failed

### Step 3: Handle failures

If implementation or validation fails for an issue:

1. Do NOT commit broken code
2. Stash or revert changes: `git checkout -- .`
3. Add a comment to the GitHub issue explaining what failed
4. Log the failure
5. Ask the user: continue to next issue (if no dependency), or stop?

### Step 3b: Version bump on phase completion

After ALL issues in the phase are completed successfully (none failed, none remaining):

1. Determine the target version from the phase number:
   - Phase 1 -> `0.1.0`, Phase 2 -> `0.2.0`, etc.

2. Update `README.md` with version note if appropriate

3. Update or create `RELEASE.txt` -- prepend a new version entry:

```
Version {version} ({YYYY-MM-DD})
---------------------------
- {VANI-xxx title}: {1-sentence summary of what was implemented}
- {VANI-xxx title}: {1-sentence summary}
...
```

4. Commit the version bump:

```bash
git add README.md RELEASE.txt
git commit -m "$(cat <<'EOF'
Release v{version} -- Phase {y} complete

All {count} issues implemented and validated.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

5. Tag the release:

```bash
git tag -a v{version} -m "Phase {y}: {phase milestone name}"
```

6. Report to user: `Phase {y} complete -> version bumped to {version}, tagged v{version}`

If some issues failed or were skipped, do NOT bump the version. Note in the execution report that the phase is incomplete.

### Step 4: Generate execution report

After all issues are processed (or on stop), generate:
`specification/phase{y}-execution-report.md`

```markdown
# Phase {y} -- Execution Report

**Date:** {date}
**Branch:** {branch name}
**Label:** {label}
**Target version:** {version}
**Executed by:** Claude Code

## Summary

| Status | Count |
|--------|-------|
| Completed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Remaining | {n} |

## Issues

| # | VANI ID | Title | Status | Commit | Files | Tests |
|---|---------|-------|--------|--------|-------|-------|
| 1 | VANI-001 | Perception call on Haiku | completed | a1b2c3d | 2 | pass |
| 2 | VANI-002 | Deterministic router | completed | e4f5g6h | 1 | pass |
| ... | ... | ... | ... | ... | ... | ... |

## Detailed Results

### VANI-001: Perception call on Haiku

**Status:** completed
**Commit:** a1b2c3d
**Files changed:**
- `src/planner/perception.py` (new)

**Validation:**
- [x] Syntax/import: pass
- [x] Tests: pass
- [x] Acceptance criteria: all pass

---

### VANI-002: Deterministic router
...

## Next Steps

{List of remaining issues not yet executed, with their dependencies}
```

Commit and push this report:

```bash
git add specification/phase{y}-execution-report.md
git commit -m "$(cat <<'EOF'
Add phase {y} execution report

{n} issues completed, {n} failed, {n} remaining.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

## Important Rules

- **One issue at a time.** Never work on multiple issues simultaneously.
- **Dependency order.** Never start an issue whose dependencies are not closed.
- **Clean commits.** Each issue = one commit. No mixing work across issues.
- **No broken code.** Only commit code that passes validation.
- **No emoji** in code, comments, UI text, or commit messages.
- **Spec is the source of truth.** Defer to the specification, architecture, and roadmap docs; do not invent behavior the spec does not describe.
- **State stays behind the repository.** Never let a personality layer reach a concrete store directly.
- **Ask on ambiguity.** If an issue description is unclear, ask the user rather than guessing.
- **Progress updates.** Print a short status line after each issue completes.
