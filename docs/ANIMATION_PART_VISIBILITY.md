# Per-animation model-part visibility (Bowser's shell, Peach's weapons, …)

**Question:** we auto-derive low-poly DObjs from the ftData table — can we do the
same for animations, so the pose/CSP renderer shows Bowser tucked in his **shell**,
Link **holding his bomb**, Peach with the right **forward-smash weapon**, instead of
the bare body with everything fused together?

**Answer (now empirically resolved): mostly YES, auto-derivable — and the viewer
already implements the decode + apply.** The per-animation swap is a subaction
command, **code 31 "Change Model State"** (= decomp `set_dobj_flags`), baked into the
fighter's action script as *data*. Only a handful of swaps are C-code-driven and need
curation (Yoshi egg, Kirby copy, Bowser/Giga **special-move** shell).

---

## The event: HSDRaw code 31 "Change Model State" == decomp `set_dobj_flags`

Decomp (`src/melee/ft/ftaction.c:686`, handler `ftAction_80071D40`, dispatch index 21):

```c
ftParts_80074B0C(gobj, cmd->u->set_dobj_flags.idx, cmd->u->set_dobj_flags.value);
```
```c
struct set_dobj_flags { u32 opcode:6; s32 idx:7 /*slot*/; s32 value:19 /*variant*/; };
```

HSDRaw descriptor (`HSDRawViewer/Scripts/command_fighter.yml`, code 31):
`Struct ID(7)` + `ExtraBitNonsense(1)` + `Object ID(18 signed)` — i.e. `idx`=Struct ID,
`value`=the 19-bit Object-ID field. Disambiguation proof (it's 31, **not** the
similar-looking code 41 "Animate Model"): the decomp triple
`set_dobj_flags(21), ftParts_80074A8C(22), ftParts_80074ACC(23)` maps 1:1 to HSDRaw's
consecutive `Change Model State(31), Revert Models(32), Remove Models(33)`. Code 41
"Animate Model" is a *separate* model-part-**animation** system (`ScriptRenderer.AnimateModel` / `ModelPartAnimations`), not visibility.

`value` (variant / Object ID, signed): `0` = default option, `1,2,…` = alternate
option, `-1` = **hide the whole slot**.

## The viewer ALREADY decodes and applies this

We don't need to invent the apply path — `HSDRawViewer` does it for the interactive
animation editor. Three pieces to reuse/port:

1. **Decode** — `GUI/Plugins/ScriptEditor/SubactionProcessor.cs`:
   ```csharp
   case 31 << 2: // struct vis change
       if (UpdateVISMethod != null)
           UpdateVISMethod(ev.GetParameter(0), ev.GetParameter(2)); // slot, variant
   ```
   (`GetParameter(0)`=Struct ID slot, `GetParameter(2)`=Object ID variant; param 1 =
   ExtraBitNonsense, skipped.) Events are parsed by `Tools/SubactionEvent.GetEvents(SubactionGroup.Fighter, struct)`.

2. **Apply** — `GUI/Plugins/ScriptEditor/ScriptRenderer.cs` `SetModelVis(slot, variant)`
   → looks up `LookupTable.CostumeVisibilityLookups[0].HighPoly[slot]` and, for each
   `SBM_LookupEntry` option `i`, `SetDObjVisible(dobj, i == variant)`. This is exactly
   the in-game `ftParts_80074B6C` loop (show selected option, hide the rest).

3. **Baseline** — `ScriptRenderer.ResetModelState()` already seeds the per-motion
   default: every HighPoly slot → option 0, **all LowPoly hidden**. That is the `_Init`
   default *and* the low-poly hide (see [CSP_LOWPOLY_HIDING.md](CSP_LOWPOLY_HIDING.md))
   in one call. Most characters' `_Init` default really is slot→0, so this matches; the
   few multi-slot/costume-conditional defaults (Link, Roy, G&W) are the only thing the
   reset can get subtly wrong.

The ftData table struct is `SBM_PlayerModelLookupTables` (ftData+0x08):
`CostumeVisibilityLookups[costume].HighPoly[slot]` → `SBM_LookupTable` →
`LookupEntries[option]` → `Entries` = DObj-index bytes
(`HSDRaw/Melee/Pl/SBM_PlayerModelLookupTables.cs`).

---

## Empirical map — which chars are data-driven vs C-code

Probed every fighter's `FighterActionTable` (ftData+0x0C → 0x18-byte
`SBM_FighterAction`; +0x00 symbol, +0x0C subaction) for code-31 events.
Reproducer: `subaction_modelstate_probe.py` (one-off `_probe_out/` scratch script, not
kept) walked `(slot, variant)` per action, parsing exact command sizes from the
`command_*.yml` so the walker was correct.

**Data-driven (code 31 → AUTO; no curation needed):**

| Char | Slots | What swaps (examples) |
|---|---|---|
| **Bowser** (PlKp) | 0 | shell (var 1) during aerials, air-dodge/escape, FallSpecial, ledge, getup, taunt/win, ItemScrew |
| **Giga Bowser** (PlGk) | 0 | identical shell data to Bowser (inherits the action set) |
| **G&W** (PlGw) | 2,5,6,7,8,10 | turn/squat (2), sleep loop (10: vars 5/4/3), SpecialN judge (5: var 6/7), SpecialAirHi/Lw parachute → hide 5–8 (var −1), intro |
| **Link** (PlLk) | 1,2 | bow/boomerang/bomb in hand during specials (1,2), item get, lose pose |
| **Young Link** (PlCl) | 1,2 | most data-driven char — sword/sheath (1) + bombs/boomerang/bow (2): item get/throw, all specials, appeals, win/lose |
| **Marth** (PlMs) | 1 | sheath/draw on HeavyGet/HeavyThrow + win poses |
| **Roy** (PlFe) | 2 | sheathed sword in Win/Lose/Intro poses (var 0) |
| **Sheik** (PlSk) | 1 | squat poses (var 0) |
| **Peach** (PlPe) | 3,4 | **forward-smash weapon** (3: var 0/1/2 = pan/club/racket, then −1 hide); AttackAirF (4) |
| **Popo / Nana** (PlPp/PlNn) | 1 | hide partner/hammer (var −1) in solo Win/Lose; Nana belay (SpecialAirHi) |

> Note: for Peach's F-smash and G&W's Judge, the *show/hide* is data (code 31) but
> *which* variant (random weapon / judge number) is chosen by C-code. For a static
> pose render, applying the event's literal variant is correct (it's what that
> animation's script encodes).

**C-code-driven (ZERO code-31 → must CURATE):**
- **Yoshi** (PlYs) — egg-roll / egg-lay shell: no subaction events at all.
- **Kirby** (PlKb) — copy-ability hats: runtime-dependent on the copied fighter.
- **Bowser / Giga special moves** — the shell during **up-B Whirling Fortress, side-B
  Koopa Klaw, neutral-B** is *not* in the subaction (aerials/escapes ARE). Source:
  `src/melee/ft/chara/ftKoopa/*Special*.c` calls `ftParts_80074B0C(gobj,0,1)` directly.
  **This is the user's exact "Bowser up-B → shell" example — a curated case.**

Everything else in the roster (Mario, Fox, Falcon, Samus, Zelda, Ganon, Pikachu,
Jiggs, DK, …) has no per-animation part swaps — `ResetModelState()` (slot→0, low-poly
hidden) is the whole story.

---

## Implemented — the animation viewer (2026-06-14)

**DONE.** When you pick an animation, the model shows its proper mesh parts (Bowser's
shell on up-B, Link's bow, …) instead of the bare default body. Verified in-render.

> **Which server actually runs the live in-app viewer:** the Electron "Animation Viewer"
> (`viewer/src/components/EmbeddedModelViewer.jsx`) is **`--embedded`** (`EmbeddedServer`,
> named-pipe IPC), launched by **`electron/viewer-manager.js`** — NOT `--stream`
> (`StreamingServer`, WebSocket), which is the headless/skin-lab/web path. Both must be
> wired, so the logic lives in a **shared `ModelPartVisibility` class** that both servers
> instantiate (`new ModelPartVisibility(_renderJObj, Log, LogError)` -> `LoadFighterData`
> after the AJ load, `OnAnimationLoaded(symbol)` in the `loadAnim` handler, `ApplyFrame`
> in the playback loop + `animSetFrame`). Don't change one server without the other.

The shared `ModelPartVisibility` (reusing the editor's engine):
- A new optional `--stream` positional arg, the **fighter-data dat** (`Pl<XX>.dat`),
  passed after the AJ file. `LoadFighterData()` reads `SBM_FighterData.ModelLookupTables`
  (the slot->variant DObj lists) and walks `FighterActionTable.Commands`, caching
  `{anim-symbol -> subaction events}` for every action carrying a code-31/32/33 event.
- `SetModelVis(slot, variant)` / `ResetModelVis()` ported from `ScriptRenderer` (operate
  on the streaming `_renderJObj`). `ResetModelVis` = every HighPoly slot->0 + low-poly hidden.
- On `loadAnim`, `SetupSubactionForSymbol` reverts to default then arms a
  `SubactionProcessor` (the editor's frame-aware walker) with `UpdateVISMethod =
  SetModelVis`. Each frame (`animSetFrame` + the playback loop) calls `ApplyModelVis`:
  reset, then `processor.SetFrame(frame)` re-fires the swaps up to that frame.
- Pointer/subroutine events (`GetPointer`) resolve against the global
  `CustomPointerValue.Values`, which the editor fills but headless doesn't -- so
  `LoadFighterData` rebuilds it from the action table's (nested) references, and
  `SubactionEvent.GetPointer` got a null-guard so an unresolved pointer degrades instead
  of NRE-ing. A swap-parse failure never breaks animation loading (caught + logged).

Plumbing: `viewer.find_fighter_data_file` + `extract_custom_character_data` (custom char
`files.fighterDataPath` -> `data_cache.dat`) resolve the dat. It must reach the exe as
arg 6 on **all THREE** launch paths (this took two misses to get right):
1. **The live in-app Animation Viewer = Electron `--embedded`.** The chain is:
   `viewer.py` paths endpoints (`/api/viewer/paths`, `paths-vanilla`, `paths-vault`) now
   return `dataFile` -> `EmbeddedModelViewer.jsx` puts it in `viewerPaths` ->
   `window.electron.viewerStart` -> `main.js` forwards options verbatim ->
   `electron/viewer-manager.js` appends it as args[6] of `--embedded` ->
   `Program.cs RunEmbeddedServer` -> `EmbeddedServer.StartAsync(…, dataFile)`. **This is
   the path the in-app viewer actually uses** — missed twice because the code is named
   "Streaming"/"viewer" but the live viewer is the *Embedded* server over a named pipe.
2. The headless/web `--stream` path: `viewer.py`'s 3 `subprocess.Popen` builders.
3. The skin-lab/programmatic path: `skin_lab._resolve_open_target` ->
   `ViewerSession(data_file=…)` -> `session.py`.

GOTCHA (the reason the live viewer showed no shell even after wiring): the fighter-data
dat `Pl<XX>.dat` is **NOT in the vanilla-assets dir** (that ships only costume dats + the
AJ). `find_fighter_data_file` must fall back to the extracted base-game files
`storage/test-base/files/Pl<XX>.dat` (same source `generate_csp` uses). The vanilla AJ +
test-base data dat are both v1.02, so symbols line up.

Null/absent data file = feature off, zero change to texture-only / stage editing.

Gated entirely on a fighter-data dat being present + a lookup table + the loaded
animation having a code-31 swap; everyone else (Mario, Fox, …) just shows the default
body (correct). (Verified with one-off `_probe_out/` scratch scripts, not kept.)

### Curated map for C-code-only swaps (also DONE, 2026-06-14)

The auto path can't see swaps with no code-31 event (driven by hardcoded special-move
C code). `Scripts/part_variant_overrides.json` (keyed by ftData root name) supplies them:
each entry is `{match: <anim-symbol substring>, slot, variant}`. `ModelPartVisibility`
loads this char's entries; `OnAnimationLoaded` applies them **only when the animation has
no auto subaction** (so auto always wins), statically for the whole animation via
`_staticOverrides` + `SetModelVis`. Shipped + verified:
- **Bowser up-B** (`SpecialHi`/`SpecialAirHi`) -> shell, limbs tucked (slot 0 var 1).
  This is the user's original "spinning around rather than in his shell" case. ✔ rendered.
- **Giga Bowser up-B** (`SpecialHi`/`SpecialAirHi`) -> shell (slot 0 var 1). ✔ rendered.
  Giga withdraws too: `ftGk_Init.c` registers **Bowser's** `ftKp_SpecialHi_*` handlers,
  which call the same `ftKp_SpecialN_80135780` withdraw. (slot 0 var 1 = Giga's shell, the
  same variant its code-31 aerials use.)
- **Yoshi Egg Roll** (`SpecialS`/`SpecialAirS`) + **egg shield** (`GuardOn`/`GuardReflect`/
  `GuardDamage`) -> egg (slot 0 var 1). ✔ rendered (the white-with-green-spots egg).
- **Kirby copy hats** intentionally NOT mapped: the variant is the *copied* fighter,
  chosen at runtime -- no static answer. Left as default (no hat) in the viewer.

### How the curated list was validated (the "method" vs the magic list)

These swaps are **not in any `.dat`** -- they're `ftParts_80074B0C` calls compiled into
`main.dol`, so HSDRaw (which only reads `.dat`) cannot see them, and HSDRaw's own
animation editor wouldn't show them either (it uses the same code-31 subaction path we
ported). The source of truth is the **decomp**. A reliable derivation method (built +
run as a one-off scratch script, not kept) extracts every `ftParts_80074B0C(slot,
variant)` call and attributes it to a move via the **call graph** -- the *trusted
state-handler that calls it*, NOT the function's own decompiler name:
- Naive "function name -> move" is **wrong**: the Bowser shell withdraw is named
  `ftKp_SpecialN_80135780` (after its address-range file `SpecialN.c`) but is *called by*
  `ftKp_SpecialHi.c` -> it belongs to **up-B**, not neutral-B (neutral-B = Fire Breath).
- The call-graph method reproduces the hand list for what's needed (Koopa up-B, Yoshi
  egg/shield) and its extra hits are all explained: G&W `SpecialLw`, Link
  `SpecialN`/`AttackAir` are already **code-31/auto**; Kirby is runtime copy; Common
  `Guard`/`Attack` + Pikachu `Init` are generic no-ops/baselines.

**Method LIMITATION (real, found the hard way): cross-character handler reuse.** The
method scans each char's dir independently, so it **missed Giga**: `ftGigaKoopa` ships no
swap code of its own -- its `ftGk_Init.c` *registers Bowser's* `ftKp_SpecialHi_*` handlers
(and many others), so Giga inherits Bowser's up-B shell withdraw. The method wrongly
concluded "Giga never withdraws"; **in-game knowledge corrected it** (Giga does withdraw),
verified by reading `ftGk_Init.c` + a render. A fully-reliable method would have to follow
each char's `_Init` state-registration table across files (incl. cross-char `ftKp_*`
refs). Lesson: the method is a strong *discovery/validation aid*, but **game knowledge +
a render is the final authority** -- which is exactly why a small verified list wins over a
naive auto-generator here.

**Why keep the list rather than auto-generate at runtime:** the C-code set is tiny and
**fixed** (Bowser + Giga up-B, Yoshi egg/shield -- the whole vanilla roster). Custom/modded
characters can't add C-code swaps (they're data mods -> their swaps are code-31 ->
already auto). So the list never needs to grow for user content; the method's role was a
one-time validator/discovery tool (the derivation scratch script above), not a runtime
dependency.

### Still open (not done)
- **CSP/pose batch renderer** (`Program.cs RunCSPGeneration`) -- same idea could feed the
  static CSP/pose renders, but that path doesn't run `SubactionProcessor`; bring the same
  `ResetModelVis` + code-31 decode (+ the curated overrides) in, keyed off the pose's anim
  symbol.
- **Subroutine frame timing**: pointer resolution is rebuilt, but if a swap ever lives
  inside a subroutine (none observed -- all swaps are in main action scripts), verify.

---

## References
- Event semantics: `src/melee/ft/ftaction.c:686` (`ftAction_80071D40`), struct
  `src/melee/lb/types.h:723` `set_dobj_flags`; dispatch table `ftaction.c:177` (index 21)
- Apply loop in-game: `src/melee/ft/ftparts.c` (`ftParts_80074B0C`/`_80074B6C`/`_80074A4C`)
- HSDRaw decode: `HSDRawViewer/GUI/Plugins/ScriptEditor/SubactionProcessor.cs`
  (`case 31 << 2`), `Tools/SubactionEvent.cs` (`GetEvents`),
  `Tools/SubactionManager.cs` (descriptors from `Scripts/command_*.yml`)
- HSDRaw apply: `HSDRawViewer/GUI/Plugins/ScriptEditor/ScriptRenderer.cs`
  (`SetModelVis`, `ResetModelState`)
- Table struct: `HSDRaw/Melee/Pl/SBM_PlayerModelLookupTables.cs`
  (`SBM_CostumeLookupTable.HighPoly` per-slot option lists);
  action table `HSDRaw/Melee/Pl/SBM_FighterData.cs` (+0x0C) +
  `SBM_FighterAction.cs` / `SBM_FighterActionTable.cs`
- Empirical probe: `subaction_modelstate_probe.py` (one-off scratch, not kept)
- Sibling (pure-data low-poly hiding): [CSP_LOWPOLY_HIDING.md](CSP_LOWPOLY_HIDING.md)
