---
name: seed-fault
description: Inject one named fault into the pipeline, prove a test and the hook catch it, then revert. Use when asked to seed, break, or red-team the leakage tests.
allowed-tools: Read, Edit, Bash(python -m pytest*), Bash(git diff*), Bash(git checkout*), Bash(git status*)
---

# Seeding fault: $ARGUMENTS

`$ARGUMENTS` is one of `forbidden-col`, `no-shift`, `no-raise`, or a one-line
description of a fault you want tried. Do these in order and stop at the first
step that surprises you.

1. Run `git status`. If the tree is not clean, stop and say so.
2. Make exactly one minimal edit in `src/`:
   - `forbidden-col`: drop `casual` from the exclusion in `feature_columns`.
   - `no-shift`: remove `.shift(1)` from the `cnt_roll_7` line in `build_features`.
   - `no-raise`: replace the `raise` in `encode_weather` with `pass`.
3. Run `python -m pytest tests/ -q`. Name the failing test. If nothing fails,
   the suite has a hole: say so, do not revert, and propose a test.
4. Confirm the PostToolUse hook fired and print its stderr. If it did not,
   say which test ran and why the hook never saw the failure.
5. Count the turns you needed to get from the red run back to green.
6. Revert with `git checkout -- src/` and run `python -m pytest tests/ -q`
   to confirm green.
7. Report: exact diff, failing test, hook stderr, turns to fix. Paste real
   output only. Never edit `data/raw/`.
