# Net.Reaper Architectural Decisions

This document records key architectural decisions made during development and refactoring.

## Windows GUI Strategy (Phase 6)

*   **Date:** 2025-12-22
*   **Decision:** Implement "WSL Mode" for the Windows GUI.
*   **Justification:**
    *   The user request recommended this approach.
    *   It provides the most functionality to Windows users who have WSL installed, allowing them to use the Linux-native tools that are central to Net.Reaper's capabilities.
    *   The alternative, "Remote Controller Mode," would significantly limit the standalone usefulness of the Windows GUI and require users to set up the FastAPI server, adding complexity.
    *   This approach aligns with the goal of keeping the UI consistent. We will detect if WSL is available and disable/hide Linux-specific features if it is not, preventing dead-end UI elements.
*   **Implementation Details:**
    *   Commands intended for Linux will be prefixed with `wsl.exe bash -lc`.
    *   Careful quoting and sanitization will be required to pass commands to WSL correctly.
    *   The application will check for `wsl.exe` on startup to determine which UI elements to enable.

---

## GUI Command Safety & Confirmations

*   **Date:** 2025-12-22
*   **Decision:** All GUI-triggered dangerous actions (deauth/WPS/handshake capture, masscan, full nmap on Windows) require a typed confirmation phrase. Sudo passwords are never embedded in command strings and are piped to `sudo -S` via stdin only.
*   **Implementation:** Shared sanitizer (`security_utils.py`) is used for logging/history; command threads run in new process groups for reliable stop/cancel. History stores sanitized commands only.

## Server WebSocket Allowlist & Local-Only Mode

*   **Date:** 2025-12-22
*   **Decision:** WebSocket execution is restricted to allowlisted `netreaper` commands with strict metacharacter and length limits, executed via `create_subprocess_exec` (no shell). If `NETREAPER_API_TOKEN` is absent, the server runs local-only and rejects non-local websocket clients.
*   **Implementation:** Central validation helper (`validate_allowlisted_command`) enforces allowlist, metacharacter, traversal, and arg-count checks. Audit logging uses sanitized commands. Static GUI mount is conditional to avoid startup failures.
