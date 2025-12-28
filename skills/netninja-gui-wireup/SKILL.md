---
name: netninja-gui-wireup
description: Verify and fix NET-NiNJA GUI wiring so every control maps to a real handler and backend action. Use when auditing UI behavior, fixing no-op buttons/tabs, or producing a control-to-handler/backend map.
---

# Netninja GUI Wireup

## Goal

Ensure every GUI control is connected to a real handler and backend action, and produce a control map that shows control -> handler -> backend -> output.

## Read First

- `netreaper_gui.py` (primary UI)
- `netreaper_gui_legacy.py` (legacy UI)
- `gui_components.py`, `gui_backend_status.py`, `gui_theme.py`
- Backend entrypoints: `job_pipeline.py`, `modules/`, `providers/`

## Workflow

1) Build a GUI control map by scanning for widget creation and signal hookups (`clicked.connect`, `currentChanged`, etc.).
2) For each control, trace the handler to the backend call and output widget. Record gaps explicitly.
3) Fix missing wiring: connect signals, implement handlers, or route to existing backend functions.
4) Validate init order: ensure widgets exist before usage (e.g., navigation lists before binding signals).
5) Remove no-op or placeholder actions, or mark as intentionally disabled with a clear message.
6) Update UI state feedback: status chips, logs, or output panes should reflect handler results.

## Output Expectations

- A control map table with file/line references.
- No GUI element that appears interactive but does nothing.
- Any fixes are tied to specific files and handlers.