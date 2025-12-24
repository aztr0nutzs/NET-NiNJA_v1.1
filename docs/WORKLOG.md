# Net.Reaper Worklog

This document tracks major changes, decisions, and how to run/test the application.

## Initial Audit (Phase 0)

*   **Date:** 2025-12-22
*   **Auditor:** Gemini
*   **Findings:**
    *   **`netreaper_gui.py`**:
        *   Identified command execution flow via `execute_command` and `CommandThread`.
        *   `sudo` handling is insecure. It relies on `pkexec` and lacks a fallback for password prompting, creating a potential failure point.
        *   Subprocess usage is mixed; `shell=True` is present in `WirelessTab.refresh_interfaces`, posing a risk.
        *   History is stored, but relies on robust sanitization.
    *   **`netreaper_gui_windows.py`**:
        *   Command execution is insecure, using `powershell.exe -Command` which is akin to `shell=True`.
        *   UI and functionality are divergent from the Linux version, with many dead-end features.
    *   **`main.py` (FastAPI)**:
        *   Websocket endpoint `/ws` has critical security flaws.
        *   Command validation logic is broken due to incorrect indentation, allowing disallowed commands to be executed.
        *   The static file mounting logic appears to be correct, checking for the directory's existence before mounting.
    *   **`requirements.txt`**:
        *   `psutil` is not listed as a dependency, which will be needed for reliable cross-platform process termination.

---

## Security Hardening Audit (2025-12-22, Phase 0)

**Scope:** `netreaper_gui.py`, `netreaper_gui_windows.py`, `main.py`

**Findings**
- GUI command execution: `execute_command` builds strings and logs them verbatim; sudo password is prompted via `QInputDialog` but command strings are reused for history and logging. Needs stronger sanitization and confirmation for dangerous operations.
- Process lifecycle: Linux `CommandThread` starts child processes without Windows creation flags; termination kills only the parent in some cases. Windows thread uses PowerShell `-Command` string; group termination is incomplete for trees.
- Wireless dangerous actions (deauth/WPS/handshake) run immediately without user confirmation.
- Windows GUI exposes Linux-only tooling; WSL detection exists but controls are not consistently disabled or rerouted.
- Server (`main.py`) static mount assumes `gui/` exists; fails startup when missing. WebSocket command validation relies on `shlex.split` allowlist but still uses `create_subprocess_exec` without stricter metacharacter checks or command length limits; token/local-only split is present but needs tightening.
- History/output: commands are stored without full sanitization of secrets; need reusable sanitizer and to ensure sudo secrets never appear.

**Next steps:** Harden GUI command execution & logging, add process-group termination, enforce confirmations, WSL handling, fix server static mount and websocket allowlist, add regression tests, update docs.

## Security Hardening Implementation (2025-12-22)

**Changes**
- Added shared sanitization/allowlist helpers (`security_utils.py`) and pytest coverage for redaction/allowlist validation.
- GUI (Linux/Windows): commands run in dedicated process groups; stop cancels child trees. Sudo passwords piped to stdin only; logging/history uses sanitized commands. Added operations console panels with status indicators and output tools. Dangerous actions (deauth/WPS/handshake/masscan/nmap full) require typed confirmation. Windows executes Linux tools via WSL when available; Linux-only buttons disabled with notices.
- Server: static mount now conditional with warning. WebSocket now enforces strict allowlist via `create_subprocess_exec`, rejects metacharacters/path traversal/length overages, logs sanitized commands, and blocks remote websocket access when no API token is set.

**How to run**
- GUI (Linux): `python netreaper_gui.py`
- GUI (Windows): `python netreaper_gui_windows.py`
- Server: `NETREAPER_PASSWORD=... NETREAPER_SECRET=... python main.py`

**Verification**
- Compile: `python -m compileall .`
- Tests: `pytest -q` (pytest not available in current environment; install via `pip install -r requirements.txt` to run)

## Phase 3: FastAPI Server Startup

*   **Date:** 2025-12-22
*   **Analyst:** Gemini
*   **Finding:** The requirement was to make the static file mounting conditional on the existence of the `gui/` directory.
*   **Resolution:** Upon review, the code in `main.py` already implements this correctly. The `app.mount` call is wrapped in an `if (BASE_DIR / "gui").exists():` block. No changes were necessary.

---
