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

## Low-poly shadows / magnifier (custom characters)

Melee renders the drop-shadow **and** the off-screen magnifier from a costume's
**low-poly** model. Custom characters often have empty low-poly DObjs → no shadow
+ empty magnifier. Full guide (cause, decomp proof, both fixes, gotchas):
**[`docs/LOWPOLY_SHADOWS.md`](../docs/LOWPOLY_SHADOWS.md)**.

- `build_lowpoly_smd.py <export.smd> <out.smd> [tris]` — decimate a costume's high
  mesh to a ~420-tri low-poly SMD (costume skeleton + weights + 1 textured group).
- `inject_lowpoly_to_vault.py <slug> <ftCode> <jointSym> <lowpoly.smd> <src.zip>`
  — inject the low-poly into every color of a vault `fighter.zip` + apply to the
  live vault. Uses HSDRawViewer `--inject-lowpoly` (surgical: fills the empty low
  DObj, remaps envelopes onto the real skeleton, preserves DObj count). **Main fix.**
- `apply_repoint_to_vault.py` / `repoint_lowpoly.py` — the quick alternative:
  repoint the low table at the high model (shadow works but redraws the full high
  model each frame = heavier). In-place ftData byte edit, reversible.
- `build_custom_iso_from_zip.py <out.iso> <fighter.zip>...` — test ISO from
  arbitrary fighter.zip(s), without touching the live vault.
