---
name: netninja-release-packager
description: Build NET-NiNJA release artifacts for legacy (Qt5) and modern (Qt6) targets, with version stamping and portable packaging. Use when creating release builds, packaging instructions, or PyInstaller specs for Windows.
---

# Netninja Release Packager

## Goal

Produce two release artifacts (legacy Qt5 and modern Qt6) with clear build commands, version stamping, and predictable runtime behavior.

## Read First

- `VERSION` for release tag
- `WINDOWS_PACKAGE_SUMMARY.md`, `WINDOWS_RELEASE_NOTES.md`, `INDEX_WINDOWS.md`
- `INSTALL_WINDOWS.md`, `QUICKSTART_WINDOWS.md`
- `requirements.txt`, `requirements_legacy.txt`, `requirements_windows.txt`
- `launch_gui.bat`, `launch_gui.ps1`, `create_shortcut.ps1`

## Workflow

1) Define build targets:
   - Legacy: PyQt5 + CPU-gated compatibility.
   - Modern: PyQt6 + full feature set.
2) Ensure requirements are clean and pinned for each target. Keep Qt5 and Qt6 separate.
3) If PyInstaller specs exist, reuse them; otherwise define consistent build commands for each target.
4) Stamp versions from `VERSION` into output naming and release notes.
5) Package artifacts with launchers and required assets. Avoid bundling unused docs or tools.
6) Document a single canonical build command per target plus a quick verification step.

## Output Expectations

- Two named artifacts: legacy and modern.
- Clear build instructions and versioned outputs.
- Notes on runtime expectations and CPU gating behavior.