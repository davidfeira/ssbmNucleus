# Debugging CSP / portrait render bugs

When a character-select portrait (CSP) or stock icon renders wrong — black blob, white
blob, missing part, blank, wrong eyes — this is the repeatable workflow to localize and
fix it. It came out of the xrunriot batch (Vader/Link-Fox/Tails) and the vault batch
(Slippy/Falcon/Mario/Luigi/Marth).

## The pipeline (what produces a CSP)

```
generate_csp.py  →  HSDRawViewer.exe --csp <dat> <out.png> [--scale N] [--head-bone B]
                    [--hide-dobjs a,b,c] [anim.anim] [scene_or_camera.yml]
```
- Renderer source: `utility/tools/HSDLib/HSDRawViewer/` (C#, OpenGL). Dev exe:
  `bin/Release/net6.0-windows/HSDRawViewer.exe`. Rebuild: `dotnet build … -c Release`.
- Shaders are RUNTIME assets in `…/bin/Release/net6.0-windows/Shader/` (editable without a
  C# rebuild), copied from the source `Shader/` on build.
- The canonical wrapper that the app calls is `backend/skinlab/costume_assets.py`
  `build_csp_and_stock`; `generate_csp.generate_csp(dat)` is the same render path.
- Hiding: a curated scene `.yml` carries baked `hiddenNodes`; otherwise `low_poly_dobjs()`
  derives the hide set from the **vanilla** `Pl<XX>.dat` ftData. `--hide-dobjs` is
  AUTHORITATIVE and *replaces* scene `hiddenNodes` (pass `--hide-dobjs 9999` to disable all
  hiding — a no-op index).

## ⚠️ Use the INSTALLED vault, not the repo

The costumes the user sees live in the installed app vault
`%LOCALAPPDATA%\SSBM Nucleus\storage\<Character>\<slot-id>-<costume>.zip` (each zip =
`Pl*Mod.dat` + `csp.png` + `stc.png`). The repo `storage/` is a separate dev copy and often
holds *different* (sometimes working) versions — diagnosing it gives false results.

## The loop

1. **Reproduce on the right file.** `python utility/tools/processor/csp_debug.py "Char/slot-id"`
   resolves the installed-vault zip, extracts the DAT, probes it, and renders it three ways
   (normal / no-hide / bundled-current) into `csp_debug_out/<slot>/`.
2. **Get ground truth.** Compare to the bundled `csp.png` and, when needed, to the model
   in-game (boot it solo — see `backend/ingame/README.md`, `backend/xrun_shots.py`). A render
   that's right in-game but wrong in CSP ⇒ the renderer mishandles valid data, not a bad DAT.
3. **Read the probe** (see cause table). The decisive splits:
   - normal broken but **no-hide fixes it** ⇒ over-hiding (cause D).
   - **UNDECODABLE > 0** ⇒ white blobs on those parts (cause E).
   - many TLUTs sharing few pixel-blobs ⇒ swatch model (cause A).
   - has `mexCostume` accessories and one's missing ⇒ cause B.
   - grey/blank eyes + has matanim ⇒ cause C.
   - blank even with no-hide ⇒ geometry not drawn (cause F).
4. **Fix in HSDRawViewer**, `dotnet build -c Release`, re-render with `csp_debug.py`, compare.
5. **Regression-check** vanilla + an unrelated costume (the render path is shared).
6. The app bakes CSPs at import; existing costumes need their CSPs **regenerated**
   (Manage CSPs / re-import) to pick up a renderer fix.

## Tools

- `utility/tools/processor/csp_debug.py` — probe + render + heuristic diagnosis (above).
- `backend/skinlab/datprobe.py` — pure-Python DAT reader (roots, JOBJ/DObj/TOBJ walk,
  `decode_image`, matanim tex-anims). Ground truth for "what does this DAT actually contain".
- Texture montage / material-color probes: see the snippets in `csp_debug.py` (`probe()`),
  reusable for ad-hoc digs.

## Known cause classes

| # | Symptom | Root cause | Status |
|---|---------|-----------|--------|
| A | Black/colored blob; many textures but few unique pixel-blobs + many TLUTs | Palette-"swatch" model (each part = a 5×5 single-color CI8, real color in its TLUT); exporter dedupes identical pixel blobs; the GL texture cache keyed on image-bytes-only collapsed them to one decode → first palette everywhere | **FIXED** — cache key = `(imageData, tlutData)` in `RenderJObj.cs` |
| B | Missing cap / Navi / cape / companion | m-ex costume accessory in `MEX_CostumeSymbol.Accessories[]`; `--csp` only rendered the main `_Share_joint` | **FIXED** — splice each `RootJoint` + follow its `AttachBone` delta in `Program.cs` |
| C | Blank / grey eyes | Real eye only in the separate `*_matanim_joint`; CSP applied no matanim | **FIXED** — matanim applied at frame 0 across all three `LoadAnimation` paths |
| D | A body part or the whole model is missing, but its textures decode fine | Over-hiding: scene `hiddenNodes` / `low_poly_dobjs` come from **vanilla** `Pl<XX>.dat` and are wrong for a custom / reordered model | OPEN — make the low-poly hide set robust for non-vanilla geometry |
| E | White blobs on specific parts (fur, mask…) | Those textures are UNDECODABLE → `PreLoadTexture` skips them → the material's white shows through | rare — C# decodes most; usually really cause G |
| F | Model renders blank / only a stray part, even with hiding disabled, but POBJ pointers exist in the DAT | **POBJ attribute list missing its `GX_VA_NULL` terminator** → `GX_DisplayList.Open()` reads ZERO primitives → no geometry. Common in imported / re-exported models | **FIXED** — `RenderDObj.cs` appends the terminator instead of discarding the pobj |
| G | Model renders a flat white / dark silhouette (form correct, no texture detail), or specific parts are flat white | Material uses **multi-texturing (2nd texmap / TEX1)** and/or **normal-based texgen (`GX_TG_NRM`, sphere/env map)**; the CSP shader's TEV emulation samples the wrong texture/coords → base texture not applied → material color shows | OPEN — needs proper GX texgen + multi-stage TEV in the shader |

Diagnostics: set `CSP_DOBJ_DEBUG=1` in the env before rendering — the renderer then logs a per-render DObj breakdown (`[cspdbg] dobjs=.. noPobj=.. hidden=.. opaPass=.. neither=..`), POBJ build skips, `[texfail]`/`[texdbg]` per texture, and `EnableBuffers FAILED`. Invaluable for D/E/F/G.

Fixed-cause details: see the `csp-renderer-edge-case-fixes` memory and `Downloads/xrunriot/BEARINGS.md`.

## Vault batch (installed vault, 2026-06-29)

| Costume | Symptom | Cause | Status |
|---|---|---|---|
| Fox `shitslippy-plfxsp` (Slippy) | only the blaster rendered | F (POBJ no NULL terminator) | **FIXED** |
| Luigi `pllgpg-pllgpg` | blank | F (POBJ no NULL terminator) | **body FIXED**; eyes still wrong (G) |
| Falcon `plcagr-plcagr01` (Gohan) | flat white silhouette | G (multi-tex + `GX_TG_NRM` texgen) | OPEN |
| Mario `plmrnr-plmrnr01` | flat dark silhouette | G (multi-tex + `GX_TG_NRM` texgen) | OPEN |
| Marth `plmsgr-plmsgr01` (Lyn) | dark + white blobs on fur/mask | G (multi-tex + `GX_TG_NRM` texgen) | OPEN |

The OPEN ones all share cause **G**: their materials use a second texture map and normal-based
texgen (the shiny suit / metal / env-map look). Fixing requires correct GX texgen + multi-stage
TEV emulation in the CSP shader — a focused, higher-risk change (could affect every model), so
it's a deliberate follow-up rather than a quick patch.
