Visual regression enforcement add-on (paste this after your main execution prompt)

VISUAL REGRESSION ENFORCEMENT (MANDATORY ADD-ON)
You must prevent “looks fine on my machine” UI drift. Implement a visual regression workflow inside this repo and wire it into CI (or at minimum a local script) so UI changes are measurable and repeatable.

Hard rules

No screenshot diffs = task not complete.

Baselines must be committed.

Diffs must fail the pipeline when beyond thresholds.

Tests must run headless (no manual clicking).

What to implement

Pick the correct visual test approach based on the UI stack

If this is a web UI (HTML/CSS/JS, PyQtWebEngine, Electron, Flask frontend, etc.): use Playwright.

If this is pure desktop GUI (PyQt/PySide/Tkinter): use pytest + snapshot images (golden images) or Playwright only if there’s an embedded webview.

If unsure, inspect the repo and choose the stack-appropriate path. Don’t guess.

Create a visual test harness that captures these exact screens/states

Main window default state (ALL tab visible)

Scan tab selected

Web tab selected

Recon tab selected

Wireless tab selected

Tools tab selected

History + Operation Console visible (post-shrink)

Attack button state visible (ensure ninja_button.png is rendered)

Progress indicator visible (ensure ninja_progress.gif rendered at least once)

Header visible (net_ninja.svg present + animated; animation is hard to diff—validate presence + a frame change or CSS animation class applied)

Enforce deterministic screenshots

Set fixed viewport/window size (e.g., 1440×900 or whatever is appropriate)

Disable system font variance where possible or bundle fonts / set fallbacks

Freeze time-dependent animations where it helps except where animation presence is being validated:

Strategy: run two screenshot passes:

pass A: animations disabled/frozen for stable diffs

pass B: animation presence asserted via DOM/class checks OR frame delta check (web) OR verifying timer/animation flags (desktop)

Add a “diff threshold”

Allow tiny anti-aliasing diffs (small % threshold)

Fail on anything beyond threshold

Add commands and docs

Add scripts:

visual:baseline (generate/update baselines intentionally)

visual:test (compare against baselines)

Update project docs with:

How to run locally

How to update baselines safely (only when changes are intended)

Where snapshots live

Common failure causes

CI integration

Add a CI job that runs visual:test

On failure, upload diff artifacts (screenshots) to CI artifacts for easy review

Acceptance criteria

Running visual:test on a clean checkout passes.

Making any UI change causes a failing diff (unless baselines updated).

Diff artifacts are produced on failure.

Baselines exist and are committed.

Test covers all required screens/states above.
