# Low-Poly Models — fixing missing shadows & magnifier on custom characters

Custom characters (and AI-rigged costumes) frequently ship with **empty low-poly
DObj slots**. In Melee that means **no drop-shadow** and an **invisible
off-screen magnifier**, because the engine renders *both* of those from the
character's low-poly model — not the main model.

This guide documents the cause (proven in the decompilation), the two fixes, and
the exact, reusable workflow to give any custom character a proper vanilla-cheap
low-poly. It was built fixing **Deoxys** (Mewtwo base) and **Lyn** (Roy base).

---

## TL;DR

```bash
# 1. extract a color model from the vault and export its high mesh
HSDRawViewer.exe --model export PlUuNr.dat PlyMewtwo5K_Share_joint PlUuNr.smd

# 2. build a ~420-tri low-poly SMD (vanilla-sized) from it
python modellab/build_lowpoly_smd.py PlUuNr.smd PlUu_lowpoly.smd 420

# 3. inject it into EVERY color model + apply to the live vault (reverts repoint)
python modellab/inject_lowpoly_to_vault.py deoxys PlUu PlyMewtwo5K_Share_joint \
       PlUu_lowpoly.smd <ORIGINAL fighter.zip>

# 4. build a test ISO and check in-game
python modellab/build_custom_iso_from_zip.py deoxys-test.iso <fighter.zip>
```

Result: shadow + magnifier render a ~420-tri mesh that **tracks the body**,
instead of nothing (or, with the quick "repoint" workaround, the full high model
every frame → lag).

---

## Why custom characters lose their shadow (decomp-proven)

The local ssbm decompilation (`C:\Users\david\projects\melee`) is the ground
truth. The character drop-shadow is rendered in `src/melee/lb/lbshadow.c`
(`lbShadow_8000F38C`). Immediately before it draws each fighter's shadow it
calls `ftDrawCommon_80081200()` (`src/melee/ft/ftdrawcommon.c`), which does:

```c
if (fighter->x5AC.xC[1] != NULL) {   // xC[1] = the LowPoly lookup
    ftParts_800750C8(fighter, 0, 0); // HIGH model OFF
    ftParts_800750C8(fighter, 2, 0); // metal OFF
    ftParts_800750C8(fighter, 4, 0);
    ftParts_800750C8(fighter, 1, 1); // LOW model ON  <-- shadow draws THIS
}
// ... HSD_ShadowStartRender() draws the now-visible (low-poly) DObjs ...
```

`ftDrawCommon_80081168()` flips it back to high afterward. The shadow render
itself (`src/sysdolphin/baselib/shadow.c` `HSD_ShadowStartRender` →
`HSD_JObjDispAll(..., RENDER_SHADOW)`) just draws whatever DObjs are currently
visible — which, during the shadow pass, is the **low-poly set**.

So:

| Low-poly state | Shadow | Magnifier |
|---|---|---|
| Real geometry (vanilla) | proper silhouette, cheap | shows the model |
| **Empty DObjs (custom char)** | **nothing** | **nothing** |
| Repointed to high DObjs | full high model = **lag** | full high model |

Vanilla Roy/Mewtwo have a real ~420-tri low-poly in those slots, so they cast a
shadow with the *exact same* visibility table that Lyn/Deoxys have — the only
difference is whether the low DObjs contain geometry.

> The shadow gate is `x5AC.xC[1] != NULL` — the LowPoly *lookup* existing, set
> from the costume table in `src/melee/ft/ftparts.c:523`. Lyn/Deoxys already have
> that (inherited from the base char), so the gate passes; the problem is purely
> that the DObjs it points at are empty.

---

## Background: the costume visibility table

Each fighter's ftData (`Pl<XX>.dat`, e.g. `PlUu.dat`) holds a
`SBM_PlayerModelLookupTables` at `ftData + 0x08`. Per costume it has four
DObj-index lists (`SBM_CostumeLookupTable`):

- **HighPoly** — the on-screen model (always rendered).
- **LowPoly** — the off-screen magnifier **and the shadow source**.
- **MetalPoly / MetalMainModel** — the Metal Box effect (references high DObjs;
  needs no separate geometry — leave it alone).

The indices point at DObjs in that costume's *model* file (`Pl<XX><color>.dat`).
Added/custom costumes reuse costume-0's table (`VisibilityIndex`, default 0).

Dump any character's table:

```bash
python -c "import sys; sys.path.insert(0,'backend'); \
from skinlab.datprobe import DatFile; d=DatFile('PlUu.dat'); \
ft=next(o for n,o in d.roots if n.startswith('ftData')); print('lookups at', ft+8)"
# or use modellab/repoint_lowpoly.py which reads + reports high/low sets
```

---

## Two approaches

### 1. Repoint (quick, but the shadow is heavy)

Point the LowPoly table at the existing **high** DObj indices ("if no low-poly
version, use the high-poly mesh index in the low-poly table" — m-ex wiki). It's a
**same-length, in-place byte edit** of the ftData table — no model surgery, fully
reversible.

```bash
python modellab/apply_repoint_to_vault.py deoxys PlUu PlUuNr.smd
```

✅ Shadow + magnifier start working immediately, zero geometry work.
❌ The shadow now redraws the **full high model every frame** (Deoxys 6118 tris ≈
14× vanilla's 420; drawn for *every* player) → lag, especially in 4-player.

Use it as a stop-gap, or for very low-poly characters (Lyn's high is only 1332
tris ≈ 3× — borderline fine).

### 2. Inject a real low-poly (recommended)

Put an actual ~420-tri decimated low-poly into the empty low DObj. The shadow is
then as cheap as vanilla and the high model is untouched. This is the proper fix.

> **Do NOT** try to add geometry by re-importing the whole model
> (`--model export`→`--model import`): IONET groups the SMD by material and the
> importer rebuilds the skeleton, which **collapses the DObj structure**
> (measured: Deoxys 42 DObjs → 4, 68 → 106 JOBJs) and breaks the visibility
> table. The injector below adds geometry surgically instead.

---

## Workflow: inject a real low-poly (step by step)

Inputs you need for a character:

| Thing | Deoxys example | How to find it |
|---|---|---|
| `slug` | `deoxys` | folder in `storage/custom_characters/` |
| `ftCode` | `PlUu` | the `Pl<XX>.dat` in `fighter.zip` |
| jointSymbol | `PlyMewtwo5K_Share_joint` | the `_joint` root in a color `.dat` (not `_matanim`) |
| low DObj index | `19` | first index of the LowPoly table (the tools read this automatically) |
| color models | `PlUuNr/Bu/Gr/Ye` | the `Pl<XX>*.zip` entries in `fighter.zip` |

**Step 1 — get an original (pre-repoint) `fighter.zip`.** The injector reverts
the table to the *original* low indices, so it needs a source whose table still
points at the real low slots. If you already repointed, grab the backup made by
`apply_repoint_to_vault.py` from `_vault_backups/<ts>-<slug>-apply/`.

**Step 2 — export one color's high model and build the low-poly SMD:**

```bash
# extract PlUuNr.dat from PlUuNr.zip inside fighter.zip, then:
HSDRawViewer.exe --model export PlUuNr.dat PlyMewtwo5K_Share_joint PlUuNr.smd
python modellab/build_lowpoly_smd.py PlUuNr.smd PlUu_lowpoly.smd 420
```

`build_lowpoly_smd.py` decimates the high mesh to ~target tris, carries weights
from the nearest high vertex, keeps the **costume's own skeleton** (so the import
preserves it), and writes a single textured group + a `.textures.json` sidecar.
All colors share geometry, so **one low-poly SMD works for every color**.

**Step 3 — inject into all colors and apply to the live vault:**

```bash
python modellab/inject_lowpoly_to_vault.py deoxys PlUu PlyMewtwo5K_Share_joint \
       PlUu_lowpoly.smd "_vault_backups/<ts>-deoxys-apply/deoxys/fighter.zip"
```

This backs up the live folder, runs `--inject-lowpoly` on each color model, keeps
the source's original ftData (so the low table points back at DObj 19 where the
geometry now lives), verifies, and atomically swaps `fighter.zip`.

**Step 4 — test in-game:**

```bash
python modellab/build_custom_iso_from_zip.py deoxys-lowpoly-test.iso \
       storage/custom_characters/deoxys/fighter.zip
```

Boot it, pick the character, and confirm: shadow is cheap (no lag), **tracks the
body** as it moves/attacks, and nothing crashes. Then reinstall in the real
project.

---

## How `--inject-lowpoly` works

`HSDRawViewer.exe --inject-lowpoly <costume.dat> <jointSymbol> <lowpoly.smd> <lowDObjIndex> <out.dat>`
(`Program.cs` → `RunInjectLowpoly`):

1. Load the costume DAT; get the root JOBJ.
2. `ImportModelHeadless(lowpoly.smd, costumeRoot)` — imports the low-poly. Because
   the SMD carries the costume's skeleton, **preserve-skeleton** kicks in.
3. **Remap joints.** The import builds a *separate* joint tree (it copies
   transforms by index — see `ModelImporter.ReplaceWithBonesFromFile`), so the
   low-poly's envelope / `SingleBoundJOBJ` references point at orphan joints. If
   left alone the shadow would **freeze at bind pose**. So we map
   `lowJoint → costumeJoint` by tree index and rewrite every reference. The map is
   keyed on the shared `HSDStruct` (`._s`), because `GetReference` hands out fresh
   accessor wrappers that aren't reference-equal.
4. Harvest the low-poly's POBJs into one chain and set the **empty** low DObj's
   `Pobj` + `Mobj`. We *fill an existing slot* — the DObj count and indices never
   change, so the visibility table stays valid.
5. Save.

The low-poly's texture comes along (a textureless DObj hangs the game). It uses
one source texture, so the **magnifier** may look slightly flat / off-color on
non-Nr variants — the **shadow** is a flat silhouette and doesn't care.

### Rebuilding HSDRawViewer

```bash
# kill any running instance + the build server first (they lock the dll)
powershell "Get-Process HSDRawViewer -EA SilentlyContinue | Stop-Process -Force"
cd utility/tools/HSDLib/HSDRawViewer
dotnet build-server shutdown
dotnet build -c Release          # exe -> bin/Release/net6.0-windows/
```

---

## Tools (in `modellab/`)

| Script / command | Purpose |
|---|---|
| `build_lowpoly_smd.py` | Decimate a costume's exported high mesh → ~420-tri low-poly SMD (costume skeleton + weights + 1 textured group). |
| `--inject-lowpoly` (HSDRawViewer) | Surgically place a low-poly into an existing costume's empty low DObj (with joint remap). |
| `inject_lowpoly_to_vault.py` | Inject into every color of a vault `fighter.zip` + apply to the live vault (backs up, atomic). **The main entry point.** |
| `apply_repoint_to_vault.py` | The quick alternative — repoint the low table to the high model (in-place table edit). |
| `repoint_lowpoly.py` | Lower-level: same-length repoint of one ftData's low table → highest-tri high DObjs. |
| `build_custom_iso_from_zip.py` | Build a test ISO from arbitrary `fighter.zip`(s) without touching the live vault. |

---

## Verification (offline)

Confirm the inject before going in-game. From `backend/`:

```python
# DObj count unchanged + the low slot is now populated:
#   walk JOBJ(+0x10 dobj, +0x08 child, +0x0C next)->DObj(+0x04 next,+0x0C pobj)->POBJ(+0x04 next)
# DObj count should stay the same; the low index's POBJ count should go 0 -> N.

# Deform correctness (the important one): every POBJ envelope joint ref must point
# INTO the costume's joint tree (not an orphan). POBJ flags @+0x0C, ENVELOPE = 1<<13;
# envelope array @+0x14; each envelope entry is (jobj_ptr@0, weight@4).
# Deoxys result: 684/684 refs -> costume bones = correct.
```

(The `--csp` render only shows bind pose, where correct and broken remaps look
identical — so the envelope-offset check is what actually proves the remap. The
real confirmation is in-game animation.)

Numbers from the Deoxys fix:

- Vanilla Mewtwo low-poly: **423 tris**. Repointed shadow: 6118 (14×).
  Injected low-poly: **419 tris** — back to vanilla cost.
- DObj count preserved (42), high model byte-untouched, 684/684 envelope refs
  remapped, confirmed in-game ("works well — no lag, tracks the body").

---

## Gotchas

- **Inject every color.** Colors share geometry but each has its own model file;
  reuse one low-poly SMD but inject into `Pl<XX>Nr/Bu/Gr/Ye` (`inject_lowpoly_to_vault.py`
  does all colors automatically).
- **Revert any repoint when injecting.** If you repointed first, pass the original
  (pre-repoint) `fighter.zip` as the source so the low table points back at the
  real low DObjs (where the geometry now is). The injector handles this.
- **Build a low-poly from the *final* model.** If the character's geometry is still
  being edited (e.g. a concurrent task), wait — a low-poly built from a stale model
  won't match.
- **Never use the `--model` export→import round-trip to add geometry** — it
  collapses the DObj structure (see "Two approaches" note above).
- **Custom char layout:** models live as `Pl<XX><color>.zip` *inside* `fighter.zip`
  at `storage/custom_characters/<slug>/`; the visibility table is in the ftData
  `Pl<XX>.dat`, not the model files. MexManager stores fighters packed in projects —
  to inspect a built result, read the exported ISO's filesystem (GCM FST), not the
  project.
- All `modellab/` work + `_vault_backups/` snapshots stay outside the live vault;
  every apply step backs up the char folder first and swaps atomically.

---

## Decomp references

- Shadow: `src/melee/lb/lbshadow.c`, `src/sysdolphin/baselib/shadow.c`
- LOD switch (high/low/metal): `src/melee/ft/ftdrawcommon.c`
  (`ftDrawCommon_80081200`/`80081168`), `src/melee/ft/ftparts.c` (`ftParts_800750C8`,
  `FtPartsVis.xC[0..4]`)
- HSDRaw structs: `HSDLib/HSDRaw/Melee/Pl/SBM_PlayerModelLookupTables.cs`,
  `Common/HSD_{JOBJ,DOBJ,POBJ,Envelope}.cs`
