---
name: netninja-qt-compat
description: Implement and maintain NET-NiNJA's Qt compatibility logic: auto-select PyQt6 vs PyQt5 based on CPU features (SSE4.1/4.2), add and honor --gui=auto|qt6|qt5, and prevent premature PyQt6 imports that crash on legacy CPUs. Use when touching GUI startup, requirements, or hardware gating.
---

# Netninja Qt Compat

## Goal

Select the correct GUI backend at runtime (auto/Qt6/Qt5), guard imports to avoid crashes, and keep requirements consistent with the selected backend.

## Read First

- `cpu_features.py` for SSE4.1/4.2 detection
- `main.py` and `netreaper_gui.py` for startup flow
- `netreaper_gui_legacy.py` for legacy GUI entry
- `launch_gui.bat`, `launch_gui.ps1` for CLI surfaces
- `requirements.txt`, `requirements_legacy.txt`, `requirements_windows.txt`

## Workflow

1) Decide backend selection rules:
   - `--gui=qt6` forces Qt6.
   - `--gui=qt5` forces Qt5.
   - `--gui=auto` uses `cpu_features.py` and forces Qt5 if SSE4.1 or SSE4.2 is missing.
2) Centralize selection logic in one function (e.g., `select_gui_backend`) that returns backend + reason.
3) Enforce import order: never import PyQt6 before the selection decision. Use conditional or local imports after selecting backend.
4) Log the decision clearly (backend + reason) before GUI startup.
5) Keep requirements aligned: Qt6 in modern requirements, Qt5 in legacy requirements. Ensure launcher docs reflect the CLI flag.
6) Add a simple diagnostic command or log line that shows the detected CPU features and selected backend.

## Output Expectations

- Runtime decision is deterministic and logged.
- Legacy CPUs never attempt PyQt6 import.
- CLI flag override works on all launch surfaces.