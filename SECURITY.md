# Net.Reaper Security

This document outlines the key security policies and features of the Net.Reaper application.

## GUI Sudo Password Handling

*   **Policy:** Sudo passwords are NEVER stored, logged, or included in command strings.
*   **Mechanism:** When a command requires `sudo`, the application will prompt the user for their password. This password is then written directly to the standard input of the `sudo -S` process. It is not stored in memory after being used, and it is never displayed in the GUI's history or logs.

## Server-Side Command Execution

*   **Policy:** The FastAPI server's WebSocket endpoint only permits a strict allowlist of commands to be executed.
*   **Mechanism:**
    *   All WebSocket connections must be authenticated with an API token or a valid JWT (local-only mode).
    *   Only allowlisted `netreaper` command roots are accepted; commands are length/arg-count limited.
    *   Commands containing shell metacharacters (e.g., `;`, `&&`, `|`, `$()`, `<`, `>`) or traversal tokens (`..`, `~`) are rejected.
    *   All commands are executed with `shell=False` using `asyncio.create_subprocess_exec` and process-group isolation for safer cancellation.

## API Token (Optional)

*   **Policy:** To enhance security for remote access, the FastAPI server can be configured to require an API token.
*   **Mechanism:**
    *   If the `NETREAPER_API_TOKEN` environment variable is set, the server will require this token for all WebSocket connections.
    *   If the token is not set, the server will run in a "local-only" mode, binding to `127.0.0.1` and rejecting non-local connections at the WebSocket layer.

## Process Isolation

*   **Policy:** Long-running tasks initiated from the GUI are executed in separate process groups.
*   **Mechanism:** This allows the application to terminate an entire tree of processes (the command and any children it spawns) reliably, preventing orphaned processes from continuing to run in the background after a "Stop" or "Cancel" action.

## User Confirmation for Dangerous Actions

*   **Policy:** Actions with high blast radius (e.g., deauth, WPS attacks, handshake capture, masscan, nmap full on Windows) require explicit user confirmation.
*   **Mechanism:** The GUI prompts the user to type `I AM AUTHORIZED` before dispatching these commands. If the phrase is not provided, the action is cancelled and logged as such.
