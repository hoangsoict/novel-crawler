# Decisions

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-08-15 | Use `AGENTS.md` as the canonical AI entry point. | Prevent instruction drift across agents. | Adapter files only link to canonical context. |
| 2026-08-15 | Keep detailed context under `.agents/`. | Make context modular and token-efficient. | Agents load only relevant rules, skills, and workflows. |
| 2026-08-15 | Do not select a functional stack during context bootstrap. | Requirements and architecture are not established. | Implementation remains blocked pending product decisions. |
| 2026-08-15 | Use English for AI context and allow Vietnamese in product docs. | Reduce token use while supporting the team language. | Avoid full bilingual duplication. |
| 2026-08-16 | Enforce pre-flight font size validation and integer font rule in `build_exe.py`. | Floating-point font sizes (e.g. 9.5) crash Tkinter on Windows with `TclError`. | `build_exe.py` automatically blocks builds if float font sizes or Tcl errors are detected. |

