# Technical Review Skill

## Use when

- Reviewing architecture, code, changes, dependencies, reliability, performance, or security.

## Checklist

- Read architecture, approved design, relevant rules, decisions, and diff.
- Check correctness, edge cases, failure modes, data integrity, and backward compatibility.
- Check trust boundaries, secrets, input validation, SSRF, rate limiting, and legal constraints.
- Check test quality and whether validation covers the changed behavior.
- Cite concrete file/line evidence; distinguish defects from suggestions.
- Prioritize findings by impact and confidence.

## Expected output

```text
Findings (severity, location, evidence, impact, recommendation)
Assumptions / Questions
Validation reviewed or run
Residual risks
```

## Memory updates

- Always after changes: `memory/SESSION_STATE.md`, `memory/CHANGELOG_AI.md`.
- Record accepted architecture choices in `memory/DECISIONS.md`.
- Record unresolved gaps in `memory/OPEN_QUESTIONS.md`.
