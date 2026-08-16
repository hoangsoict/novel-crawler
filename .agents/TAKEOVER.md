# Takeover Guide

## Read in order

- `AGENTS.md`
- `.agents/PROJECT_INDEX.md`
- `.agents/ARCHITECTURE.md`
- `.agents/memory/SESSION_STATE.md`
- `.agents/memory/DECISIONS.md`
- `.agents/memory/OPEN_QUESTIONS.md`
- Relevant rules, skill, workflow, and `docs/` files

## Initial commands

Run only commands available for the selected stack:

```text
git status --short --branch
git log -5 --oneline
git diff --stat
```

Then inspect the repository tree and discover project-specific validation commands from committed configuration. The workspace is not currently a Git repository; do not initialize Git without user approval.

## Do not do autonomously

- Do not invent business behavior, supported sources, or acceptance criteria.
- Do not add dependencies, credentials, external services, or telemetry without approval.
- Do not perform destructive Git/filesystem actions or rewrite shared history.
- Do not crawl external sites or use production data without confirmed authorization.
- Do not claim validation that was not run.

## Before work

Follow `.agents/workflows/START_SESSION.md`, then `.agents/workflows/BEFORE_CHANGE.md` for modifications.
