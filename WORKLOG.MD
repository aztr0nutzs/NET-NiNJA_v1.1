# Worklog

## 2025-12-13
- Added a dependency-free holographic WiFi discovery map UI (`ui/holo_map/`) and a local Python map server (`bin/netreaper-map`).
- Added `wifi_scan_json` in `lib/wireless.sh` and exposed it via `netreaper wifi scan`.
- Added `netreaper wifi map` to serve the UI and read `~/.netreaper/output/wifi_scan_latest.json`.
- Updated documentation and Bats tests.

### How to run
1) `netreaper wifi scan <iface>`
2) `netreaper wifi map 8787`
3) Open `http://127.0.0.1:8787/`

## 2025-12-17
- Implemented full wizard modules (`web_wizard.sh`, `creds_wizard.sh` and `wifi_takeover_wizard.sh`) with progress display, checkpoint/resume support and lite‑mode awareness. The credential and WiFi wizards now support reduced wordlists when `NR_LITE_MODE` is set and save progress so interrupted sessions can resume.
- Added `is_lite` and `get_wordlist` helpers in `lib/core.sh` to centralise lite‑mode behaviour and provide small wordlists automatically.
- Added new `lib/monitor.sh` providing `monitor_resources` and `monitor_loop` functions to monitor CPU and memory usage and automatically enable lite mode when thresholds are exceeded.
- Enhanced scanning module to skip full and UDP scans in lite mode and to prefer masscan for quick scanning.
- Refactored `netreaper` CLI to properly expose the pipeline queue commands and moved the `queue` case outside of the stress section.
- Improved `creds_wizard.sh` and `wifi_takeover_wizard.sh` to use checkpoints, show progress and select smaller wordlists in lite mode. Added more robust enumeration logic and logging.
- Secured the remote API (`server/main.py`): JWT tokens now include an expiry, authentication uses an environment variable for the password, commands executed over the websocket are restricted to the NetReaper CLI and the working directory is configurable via `NETREAPER_ROOT`.
- Added new GUI features in `netreaper_gui.py`: a `WIZARDS` tab exposes the CLI wizards with a progress bar, a `JOBS` tab reads the pipeline job queue and displays statuses, and the HUD now indicates when Lite mode is active. Toggling Lite mode updates the HUD label accordingly.

### How to run
1) Run any wizard via the GUI under the `WIZARDS` tab (e.g. Web Recon Wizard). Progress updates as each stage completes.
2) Manage queued jobs via the CLI: `netreaper queue add --file job.yml`, then check the `JOBS` tab to view status.
3) Toggle Lite mode via the toolbar and observe the HUD status update.