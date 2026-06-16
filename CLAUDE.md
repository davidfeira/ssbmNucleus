# CLAUDE.md — ssbmNucleus

Melee modding tool (Electron + Flask + React). Builds modded ISOs via
MexManager/MexCLI (C#) + HSDRaw; manages costumes, stages, custom characters,
patches. See the user auto-memory `MEMORY.md` for architecture/paths.

## ⚠️ Testing a built ISO in-game (crash tests, move/side-B repros, screenshots)

**Use the solo, no-CPU, no-cursor engine in [`backend/ingame/`](backend/ingame/README.md).**
It memory-writes the player block and relaxes the "Ready to Fight" gate to load
the match **alone**. Template: **`backend/fsm_crash_probe.py`** (run from
`backend/` with `python`). Read [`backend/ingame/README.md`](backend/ingame/README.md) first.

```
patch_one_player(d) → nav_to_css → force_time_infinite
→ write_solo_player(d, ckind, color)  # ckind = external CSS id; 1st m-ex fighter = 0x1A
→ warp_to_stage_select(d) → StageCursor.force_select(stage)   # all memory, no cursor
```

**Do NOT** drive the CSS cursor or add a CPU (`tests/dolphin/` +
`tests/nucleus/cl_match.py` + `pipe.js cpustep`) for gameplay tests. That path is
slower (cursor sweep + add-CPU), and the **CPU attacks you and moves the camera,
ruining move/crash repros**. The cursor path is only for testing the CSS/SSS
**UI itself** (icon/grid/menu mods). This mistake is recurring — don't repeat it.

## m-ex / Ace-build gotcha

The bundled m-ex codes are **~current with public upstream** (`akaneia/m-ex`
master `codes.gct` ≈ 64 KB; ours ≈ the same). We are NOT behind public m-ex.
But the **Ace Build** (`storage/xdelta/1e906281.xdelta`) ships a **custom,
extended m-ex core** (`codes.gct` ≈ 77 KB) that is **not in public upstream** and
**not a `codes.ini` toggle code**. Characters authored in the Ace Build (e.g.
Metal Mario's cape) depend on that custom core: re-installed onto a vanilla/public-
m-ex base they crash with `assertion "0" failed in m-ex ... item not initialized`
even though the fighter data + item tables are byte-identical to the working build.

→ For Ace-sourced characters, **build on the Ace base**, not vanilla. Pulling
public upstream m-ex will NOT add the Ace core. Note `codes.ini` is itself a local
fork (bigger than upstream) — don't blindly overwrite it. Safe codes refresh +
backup/restore: `scripts/mex_codes.py` (run `status` first; it never touches the
current version without a backup).
