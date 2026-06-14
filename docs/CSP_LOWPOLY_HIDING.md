# Hiding low-poly meshes in CSP / head-shot renders (any character)

When HSDRawViewer renders a portrait (`--csp`), it draws **every DObj in the
model** — including the off-screen **low-poly** mesh (the magnifier/shadow body)
that the game normally never shows in play. Left visible, that low-poly geometry
pokes through the portrait (a second, blockier body fused into the real one).

So a clean CSP must **hide the low-poly DObjs** during the render. The pose/scene
YAML carries this as a `hiddenNodes:` list, and `Program.cs:ApplyHiddenNodes`
applies it as **DObj indices**:

```csharp
foreach (int dobjIndex in hiddenNodeIndices)
    if (dobjIndex >= 0 && dobjIndex < renderJObj.DObjCount)
        renderJObj.SetDObjVisible(dobjIndex, false);   // <-- DObj index, not bone
```

> They're called "nodes" in the YAML but they are **DObj indices** — the same
> index space the in-game part-visibility table uses. Not JOBJ/bone indices.

---

## TL;DR — there is no list to "find"

The low-poly DObj set is **stored in every fighter's data file**, not something to
look up in a hand-maintained table. Read it straight from `Pl<XX>.dat`:

- `Pl<XX>.dat` ftData holds a `SBM_PlayerModelLookupTables` at **ftData + 0x08**.
- Per costume it has a **HighPoly** DObj list (the on-screen model) and a
  **LowPoly** DObj list (magnifier/shadow). They partition the model's DObjs.
- **`hiddenNodes` for a clean CSP = costume-0's LowPoly set** (≡ every DObj not
  in HighPoly). This reproduces exactly what the engine shows in normal play.

This works for **vanilla and custom characters alike**, because every custom
character ships its own `Pl<XX>.dat` with this table (recolors inherit the base's
table; AI-rigged characters get a valid table built by `modellab/rig.py`). No
per-character guesswork, no hardcoded list.

The reader already exists: `modellab/extract_visibility.py` (writes
`visibility_tables.json`) and `modellab/rig.py:load_low_indices()`.

---

## Why the old per-character `scene.yml` lists don't generalize

`utility/tools/processor/csp_data/<Character>/scene.yml` carries a **hand-authored**
`hiddenNodes:` block — someone toggled DObjs off in the viewer until the portrait
looked right. Those indices are valid **only for that exact model**. Two failure
modes when reused:

1. A different model has its low-poly at **different DObj indices** → the list
   hides the wrong things.
2. Index ranges drawn by hand are approximate (over/under-hide).

This is exactly the **Giga Bowser** bug. `generate_csp.find_character_assets()`
poses Giga with **Bowser's** scene (`folder_name = 'Bowser'`), so Giga inherits
Bowser's hand-list — which is calibrated for a *different* model:

| | Bowser `PlKp` (115 DObjs) | Giga `PlGk` (124 DObjs) |
|---|---|---|
| HighPoly (show) | 0–28, 78–99, 101–114 | 0–24, 59–71, 83–108, 110–111, 113–114, 116–117, 119–120, 122–123 |
| **LowPoly (hide)** | **29–77, 100, 103, 106, 109, 112** | **25–58, 72–82, 109, 112, 115, 118, 121** |
| `scene.yml` hides | 29–97, 100, 103, 109–111 (hand) | *(borrows Bowser's →)* 29–97, 100, 103, 109–111 |

Applying Bowser's list to Giga:
- **Leaves Giga low-poly visible:** 25–28, 112, 115, 118, 121 (never hidden) →
  blocky mesh pokes through.
- **Hides real Giga body:** 59–71, 83–97, 110, 111 are Giga *HighPoly* but fall in
  Bowser's hidden range → parts of the actual portrait go missing.

The correct Giga hide list is just Giga's own LowPoly set:
`25–58, 72–82, 109, 112, 115, 118, 121`.

---

## The reader (read the table from any `Pl<XX>.dat`)

The lookup table is reloc-encoded (vanilla dats pad the arrays, so a length field
can over-count — only trust a field that is itself in the reloc table). Mirror
`extract_visibility.py`:

```python
# ftData + 0x08 -> lookups; lookups: u32 count, ptr array of 0x10-byte costume entries
# each costume entry: +0x00 HighPoly table, +0x04 LowPoly table
#   table: u32 count, ptr array of 0x08-byte entries; each entry: u32 n, ptr to n DObj-index bytes
def low_dobjs(plxx_dat):                     # -> sorted list of DObj indices to hide
    d = DatFile(plxx_dat)
    ft = next(o for n, o in d.roots if n.startswith('ftData'))
    lookups = d.ptr(ft + 0x08)
    vis_arr = d.u32(lookups + 0x04) if (lookups + 0x04) in d.relocs else None
    entry0  = vis_arr                        # costume 0 (added costumes reuse it)
    low_tbl = read_table(d, entry0, 0x04)    # see extract_visibility.read_table
    return sorted({i for e in (low_tbl or []) for i in e})
```

`_probe_out/giga_vis_probe.py` is a runnable reproducer (dumps High/Low for
`PlKp`/`PlGk` and the model DObj counts).

### Index-space proof (why this is the same space `SetDObjVisible` wants)
- Bowser table references max DObj 114 → 115 DObjs; the model `PlKpNr.dat` walks
  to **exactly 115 DObjs**; the C# bound is `renderJObj.DObjCount`. They match.
- Bowser's *hand-authored* `hiddenNodes` starts at **29** — the exact first index
  of the table's LowPoly set. A hand list built by eye in the viewer would only
  line up with the table if the viewer's DObj indexing == the table's. It does.
- The in-game engine uses these same indices against the same model
  (`ftParts_800750C8` flipping High/Low — see `LOWPOLY_SHADOWS.md`).

---

## How it's implemented (done)

Auto-derived at render time, for every render, via a new HSDRawViewer flag:

1. **`--hide-dobjs a,b,c`** (`Program.cs` `RunCSPGeneration`, mirrors
   `--collapse-bones`). It is **authoritative**: it resets every DObj visible,
   then hides exactly the given indices — so it *replaces* whatever `hiddenNodes`
   the (possibly borrowed) scene applied, rather than unioning with it. Works in
   both normal `--csp` and `--head-shot` modes (the head-shot has no scene, so
   this is the only way to hide low-poly for the stock head crop).
   > Gotcha that cost an hour: the scene's `hiddenNodes` are applied to the
   > `renderJObj` during scene load, so merely clearing the parsed *list* before
   > the apply isn't enough — you must reset all DObjs visible first. Verified by
   > logging `GetHiddenDObjIndices()` at screenshot time.

2. **`generate_csp.low_poly_dobjs(dat, character)`** reads the costume-0 LowPoly
   set from the fighter ftData and passes it as `--hide-dobjs` on both the CSP and
   head-shot renders. ftData is located as a sibling `Pl<XX>.dat` next to the
   model, else the vanilla copy in `storage/test-base/files/Pl<code>.dat`
   (`CHARACTER_CODES[character]`). If the table can't be read it returns None and
   the render falls back to the scene's own `hiddenNodes` (no regression).

Verified no vanilla regression: rendering Bowser with its derived set vs its
hand-authored scene list is visually identical (mean pixel diff ~6, the derived
set is just the truer low-poly set). Giga (which borrows Bowser's scene) now hides
its *own* low-poly (`25–58, 72–82, 109, 112, 115, 118, 121`) instead of Bowser's
mismatched `29–97`.

> Not done: Giga's CSP still uses **Bowser's camera** (it borrows Bowser's scene),
> which is tuned for Bowser's smaller body and crops the larger Giga to a
> head/upper-body view. That's a camera-framing follow-up, independent of the
> (now-fixed) low-poly hiding. The **stock** icon is unaffected — it comes from
> the auto-framed `--head-shot` render via `stock_gen`, not the CSP camera.

---

## Caveats
- **The table indexes the MODEL's DObjs.** It's valid only when the model's DObj
  layout matches the table — true for **recolors** (same structure as base) and for
  **`rig.py`** output (it places low-poly at the LowPoly indices and dummy-fills the
  rest by construction). A raw `--model import` that *collapsed* the DObj structure
  (see `LOWPOLY_SHADOWS.md`) would desync the table → don't trust it there.
- **Added/extra costumes reuse costume-0's table** (`visibilityIndex`, default 0),
  so reading costume 0 is correct for recolors.
- `extract_visibility.py`'s `CODES` list is the **playable roster only** — it omits
  internal fighters like `PlGk` (Giga) and bosses. For those, and for custom
  characters, read the table **directly from the character's own `Pl<XX>.dat`**
  rather than from `visibility_tables.json`.
- **Verify with a render.** Bind-pose/portrait differences are subtle; the real
  confirmation is eyeballing the generated PNG (Read it) — consistent with how the
  shadow low-poly work is signed off in-game.

## References
- Apply path: `utility/tools/HSDLib/HSDRawViewer/Program.cs`
  (`RunCSPGeneration`, `ApplyHiddenNodes` ~L5495)
- Reader: `backend/modellab/extract_visibility.py`, `backend/modellab/rig.py`
  (`load_low_indices`, `load_high_indices`)
- CSP pipeline: `utility/tools/processor/generate_csp.py`
  (`find_character_assets` redirects Giga → Bowser at L207–210)
- Sibling concern (in-game shadow/magnifier from the same table): `LOWPOLY_SHADOWS.md`
- Table struct: `HSDLib/HSDRaw/Melee/Pl/SBM_PlayerModelLookupTables.cs`
