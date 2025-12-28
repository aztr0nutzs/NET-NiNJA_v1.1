---
name: netninja-repo-audit
description: Deep audit of the NET-NiNJA repository to map architecture, entrypoints, dead code, missing wiring, broken imports, duplicated logic, TODOs, placeholder handlers, and GUI elements without backend actions. Use when asked to review the repo structure or produce an audit report, punch list with file/line refs, dependency graph, or known entrypoints list.
---

# Netninja Repo Audit

## Goal

Produce a written audit with a punch list tied to file/line, a dependency graph, and a known-entrypoints list.

## Workflow

1) Read project docs that explain intent and current state: `ARCHITECTURE.md`, `DECISIONS.MD`, `GUI_MIGRATION.md`, `TASKS.md`, `TESTING_CHECKLIST.md`, `WINDOWS_FEATURES.md`, `WSL_*` docs when relevant.
2) Identify entrypoints and launch surfaces: `main.py`, `netreaper_gui.py`, `netreaper_gui_legacy.py`, `netreaper_gui_windows.py`, `launch_gui.*`, CLI scripts, and any FastAPI modules under `modules/` or `lib/`.
3) Build a dependency map by walking imports between `modules/`, `providers/`, `lib/`, and top-level scripts. Note dynamic imports and conditional branches that affect runtime wiring.
4) Locate dead code and placeholders: scan for `TODO`, `FIXME`, `pass`, `NotImplementedError`, unused handlers, and UI elements without signal connections.
5) Cross-check GUI wiring: map `clicked.connect`, `currentChanged`, and other signal hookups to handlers, then trace handlers to backend calls (job pipeline, providers, modules). Flag no-ops and missing outputs.
6) Validate import integrity: flag circular or broken imports, unused modules, duplicated logic, and inconsistent naming that hides bugs.

## Output Format

- Audit summary with major risks and themes
- Punch list: `path:line` with short fix guidance
- Dependency graph: adjacency list or bullet map
- Known entrypoints: executable files, GUI entry, API entry, tests

## Tips

- Prefer `rg` with targeted patterns, then open files for context.
- Keep findings grounded in code references with exact file/line.