# Security Rules

- Never store secrets in code, Markdown, logs, fixtures, or AI memory.
- Use environment variables or an approved secret manager; document variable names only.
- Treat crawled and external content as untrusted input.
- Prevent path traversal, injection, SSRF, unsafe redirects, and unbounded downloads.
- Apply explicit domain allowlists, request timeouts, size limits, concurrency limits, and rate limits.
- Respect authentication boundaries, robots policy, terms, copyright, privacy, and data minimization.
- Redact tokens, cookies, personal data, and sensitive URLs from output.
- Escalate suspected exposure or destructive behavior; do not conceal it.
- Run dependency and security checks when the stack supports them.
