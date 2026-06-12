# Model-lab harness

Dev/QA scripts for the AI Model Studio rigging pipeline (`backend/modellab/`).
These are lab tools, not app code — they drive the pipeline end-to-end against
real ISOs and capture in-game screenshots for visual QA.

The scripts' working copies live at the repo parent (`../modellab/`) next to
their heavy artifacts (rig kits, test ISOs, screenshots, outputs), all of which
are derived/regenerable and not committed. Paths inside are absolute to that
layout.

## The main loops

- `rig_cross.py <slug> <PlCode> [tag]` — rig a vanilla character's model onto
  Fox's skeleton (the cross-character stress test: marth/PlMs, ganondorf/PlGn,
  falco/PlFc), import, and build a bootable test ISO.
- `pause_capture.py <iso> <out.png> [costume_index] [still|nopause|strip|move]`
  — boot the ISO, start a solo match via the in-app memory-select engine, move,
  pause, and screenshot (or grab a 6-frame animation strip).
- `map_characters.py` — export every character's rig kit + audit stats
  (`character_map.json`).
- `extract_visibility.py` — per-character costume ModelVisibilityTables →
  `backend/modellab/visibility_tables.json`.
- `build_user_iso.py` / `test_blueprint_pipeline.py` / `test_save_intake.py` —
  single-costume ISO build, blueprint-pipeline drive, live intake save check.

## Diagnostics

`audit_*` / `probe_*` / `trace_head.py` / `compare_*` — weight/envelope/pose
forensics used while debugging cross-rig artifacts. `make_staircase.py` /
`make_bonemap.py` build diagnostic costumes (per-DObj placement / per-bone
ownership). `viz_group.py` renders a single mesh group. `crop_shots.py` crops
capture screenshots around the character.
