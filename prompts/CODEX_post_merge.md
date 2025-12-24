Post-merge verification prompt (paste this after Codex finishes + after merge)

CODEX POST-MERGE VERIFICATION PROMPT (MANDATORY RECHECK)
You are now performing a post-merge verification audit to confirm nothing regressed and the merged result fully satisfies the original requirements.

Rules

You must re-check the merged codebase as if you’ve never seen it before.

You must verify both: (1) code wiring and (2) runtime-visible behavior.

If anything is off, you must open a fix PR (or provide exact patch-ready changes) immediately.

Verification checklist (must all pass)

A) Layout & scrolling

Confirm ALL category layouts (ALL/Scan/Web/Recon/Wireless/Tools) show the maximum options possible without scrolling.

If scrolling exists, confirm it is unavoidable and minimal.

Confirm History + Operation Console are shrunk, neat, and still fully functional (scroll inside panels works, logs not truncated incorrectly).

B) Navigation

Confirm top nav contains Scan/Web/Recon/Wireless/Tools.

Confirm left sidebar does NOT contain duplicates of those nav buttons.

Confirm left sidebar replacements are different, relevant, useful, and fully wired (no dead clicks).

C) Color enforcement

Confirm full background is pure black everywhere (no grey containers, no grey canvas, no default widget background leaking).

Confirm Scan:

neon green is used consistently for scan-related tasks/options

electrified animation exists and is performant

Confirm Attack/offensive:

bright red consistently

all attack-related actions use ninja_button.png (no exceptions)

D) Branding & assets

Confirm header text (“THE REAPER IS WATCHING”) is fully removed.

Confirm net_ninja.svg is present, prominent, and animated.

Confirm purple skull/bones removed and replaced with an animation container ready for a future GIF.

E) Progress indicators

Confirm all progress indicators use ninja_progress.gif.

Confirm progress shows where needed and properly starts/stops (no stuck overlay, no double overlay, no forever spinner).

F) Regression suite

Run unit/integration tests (whatever exists).

Run the visual regression test suite (visual:test).

Confirm CI passes (if CI config exists).

Confirm artifacts generated on failure are correct (simulate a diff if needed).

G) Dead code / leftovers

Confirm no unused assets (old skull image, unused button images, unused CSS) remain.

Confirm no orphaned styles (grey backgrounds, old header styles) remain.

Confirm no duplicate IDs/classes or conflicting theme rules remain.

Deliverables

Provide:

A short “PASS/FAIL” for each section A–G

Exact file paths touched (if fixes are needed)

If any FAIL: implement the fix completely and ensure tests + visual diffs pass

