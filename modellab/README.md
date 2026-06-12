# Model lab

Dev/QA harness for the AI Model Studio rigging pipeline (`backend/modellab/`).
These scripts drive the pipeline end-to-end against real ISOs and capture
in-game screenshots for visual QA.

Heavy artifacts live here too but are **not committed** (see .gitignore):
test ISOs, `rigkits/` (per-character SMD exports + pose dumps, regenerate via
`map_characters.py` + `--dump-pose`), `out/`, `shots/`.

## The main loops

- `rig_cross.py <slug> <PlCode> [tag]` — rig a vanilla character's model onto
  Fox's skeleton (cross-character stress test), import, build a bootable ISO.
- `pause_capture.py <iso> <out.png> [costume_index] [still|nopause|strip|move]`
  — boot the ISO, start a solo match via the in-app memory-select engine,
  move, pause, screenshot (or grab a 6-frame animation strip).
- `preview_mesh.py <mesh> <out.png>` — render a raw GLB/OBJ/SMD without
  rigging (the studio's mesh-approval render, lab-side).
- `map_characters.py` — export every character's rig kit + audit stats.
- `extract_visibility.py` / `extract_dynamics.py` — vanilla Pl*.dat →
  `backend/modellab/visibility_tables.json` / `dynamic_bones.json`.
- `test_skeleton_parts.py` — validate the body-part labeler against
  `bone_names_reference.json` (community bone names, Mario + Captain).
- `build_user_iso.py` / `test_blueprint_pipeline.py` / `test_save_intake.py` —
  single-costume ISO build, blueprint-pipeline drive, live intake save check.

## Diagnostics

`audit_*` / `probe_*` / `trace_head.py` / `compare_*` — weight/envelope/pose
forensics. `make_staircase.py` / `make_bonemap.py` build diagnostic costumes
(per-DObj placement / per-bone ownership). `viz_group.py` renders one mesh
group; `crop_shots.py` crops captures around the character.
