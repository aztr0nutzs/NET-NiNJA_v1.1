# Decisions

## 2025-12-13 — Holographic WiFi map implementation approach
- Chose a dependency-free canvas renderer instead of Three.js so the UI works offline and doesn't require bundling large vendor libraries.
- Chose a tiny `python3` HTTP server for the UI/API because NETREAPER is Bash-first and Python is commonly available on Linux security distros.
- Scan export prefers `nmcli` (managed mode) and falls back to `iw` (root) to balance portability vs privilege requirements.

## 2025-12-17 — Wizard, Pipeline and GUI enhancements

- **Bash wizards with resumable state** — Instead of rewriting the wizards in Python, the new `creds_wizard.sh` and `wifi_takeover_wizard.sh` were enhanced in Bash.  Checkpoint files under `~/.netreaper/config/checkpoints` allow interrupted runs to be resumed by storing the current step number in JSON.  This keeps the logic simple and consistent with the rest of the shell scripts.
- **Lite mode as environment flag** — The decision was made to implement lite mode via an environment variable (`NR_LITE_MODE`) and centralise the behaviour in `lib/core.sh`.  Modules can call `is_lite` and `get_wordlist` to adjust scanning aggressiveness and wordlist sizes.  This avoids scattering conditional logic throughout the codebase.
- **Resource monitoring** — A simple Bash-based monitor reads `/proc/stat` and `/proc/meminfo` to compute CPU and memory usage.  When thresholds are exceeded multiple times the monitor enables lite mode automatically.  Python's `psutil` was avoided to minimise dependencies.
- **Secure remote API** — The previous remote API allowed arbitrary command execution using a static token.  JWT tokens now include an expiry and are generated using an environment defined secret.  Only commands that invoke the NetReaper CLI are permitted and the working directory is controlled via `NETREAPER_ROOT` to limit the attack surface.
- **GUI extensions** — The PyQt GUI was extended by adding dedicated `WIZARDS` and `JOBS` tabs rather than overloading existing categories.  Each wizard runs the CLI asynchronously in a `CommandThread` and the output is parsed for progress markers.  A HUD status indicator reflects lite mode state.  This approach reuses existing infrastructure instead of writing a separate wizard engine.