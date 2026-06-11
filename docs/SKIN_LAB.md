# Skin Lab — AI / scriptable skin creation

A REST surface over the Skin Creator's machinery so an AI agent (or any
script) can create character skins end-to-end: open a costume in a live
HSDRawViewer, fetch/replace textures, run the color-palette tool, reposition
the 3D camera and grab rendered frames, pose real animations, and save the
result back to the vault as a new skin.

All endpoints live under `/api/mex/skin-lab/` on the Nucleus backend. One
session at a time (it owns a real OpenGL window — you will see it appear).

Implementation: `backend/blueprints/skin_lab.py` (routes),
`backend/skinlab/session.py` (HSDRawViewer `--stream` WebSocket client),
`backend/skinlab/palette.py` (numpy port of the UI palette tool).

## Typical agent loop

```text
POST /open {"character":"Fox","skinId":"c9-plfxc9"}    -> textures listed
GET  /frame                                            -> look at the model
GET  /texture/3                                        -> inspect a texture
POST /texture/3 (file or {data: b64})                  -> paint / replace it
POST /palette/analyze {"maxGroups":5}                  -> color groups
POST /palette/apply {"adjustments":[{"index":2,"hueShift":105}]}
POST /camera {"rotY":150,"scale":1.6}                  -> view the back
GET  /frame                                            -> verify the change
POST /save {"name":"My Colorway"}                      -> new vault skin
POST /close
```

## Endpoints

### Session
- `POST /open` — body one of:
  - `{character, skinId}` — a vault skin. `character` accepts canonical names
    (`"Fox"`) AND custom-character pseudo keys
    (`"custom_characters/<slug>/skins"`, `".../costumes"`).
  - `{character, costumeCode}` — a vanilla costume (e.g. `"PlFxNr"`).
  - `{datPath}` — any costume DAT on disk (optional `character` for scene/AJ).
  Returns the texture list (index/name/size), camera state, animation info.
- `GET /status` — `{open, session}`.
- `POST /close` — kill the viewer, drop all state.

### Textures
- `GET /textures` — list + which indexes have been edited.
- `GET /texture/<i>` — full-res PNG (the edited version once you've pushed one).
- `POST /texture/<i>` — multipart `file` or JSON `{data: <base64 png>}`;
  auto-resized to the texture's native size. Shows up in the 3D view live.

### Viewing the model
- `POST /camera` — absolute `{rotX, rotY, scale, x, y}` (degrees; scale = zoom,
  bigger is closer) or relative `{deltaRotX, deltaRotY, deltaZoom, deltaX, deltaY}`.
- `GET /frame?fresh=2&width=&height=` — current render as JPEG. `fresh` waits
  that many new frames so your latest changes are in the shot.
- `GET /anims` — the character's real animation symbols (from the AJ archive).
- `POST /anim` — `{symbol}` to load, `{frame}` to pose a frame (pauses),
  `{playing: true|false}`.

### Color palette tool (same algorithm as the UI)
- `POST /palette/analyze {maxGroups?: 8}` — clusters every texture's pixels
  into hue groups; returns `[{index, centerHue, hueRange, pixelCount,
  displayColor, avgSaturation, avgLightness}]`. Snapshots current textures.
- `POST /palette/apply {adjustments: [{index, hueShift?, saturationShift?}]}` —
  recolors from the snapshot (shifts are ABSOLUTE, so re-applying with new
  values replaces, never stacks). Lightness is untouched so shading survives.
- `POST /palette/reset` — push the snapshot back.

### AI engine (texture generation)
- `POST /generate-texture {prompt, index?, style?: 'scene', tier?, model?,
  seed?, width?, height?, name?}` — generates an image via the VENDORED AI
  engine (`backend/aiengine/`): local diffusion in a managed runtime, or an
  OpenRouter image model. Which model runs is decided by the task-tier
  resolver (`aiengine/routing.py`): `tier` defaults to `standard` (seamless
  tile swatch) or `strong` when `style:'scene'` (coherent backdrop). Users
  map tiers to models in Settings → AI Studio; an explicit `model` (registry
  id like `sd-turbo`, or an OpenRouter slug containing `/`) overrides. With
  `index`, the result is resized onto that texture in the open session;
  without, it just returns `imagePath`. First local call loads the model —
  slow. Every generation is ledgered to `storage/ai_runs.jsonl` (stats:
  `GET /api/mex/ai-engine/stats`).
- Engine management lives under `/api/mex/ai-engine/`: `status`, `models`
  (catalog + downloaded/fit/measured-speed), `models/<id>/download|delete|
  toggle`, `install` (managed Python+torch runtime), `routing` (tier→model),
  `resolve` (preflight escalation notices), `stats`.
- FULLY-LOCAL mode: planner ids prefixed `ollama:` (e.g. `ollama:qwen3:8b`)
  run the planning LLM through a local Ollama server (`NUCLEUS_OLLAMA_URL`,
  default localhost:11434) with `format:json` + `keep_alive:0` — the LLM
  unloads immediately after each call so the diffusion model gets the GPU.
  No OpenRouter key needed when both planner and image models are local.
  `GET /api/mex/ai-engine/planners` lists installed Ollama models; the
  studio planner pickers append them automatically. Benchmarked with
  `scripts/skinlab_local_planner_test.py`: qwen3:8b = 6/6 valid plans, full
  character-region coverage, ~5s/plan, 6GB VRAM, clean unload. The vision
  REVIEW pass needs a vision-capable local model (e.g. gemma3:4b,
  qwen2.5vl) — with a text-only planner it's skipped gracefully.
- Dev escape hatch: set `NUCLEUS_AIENGINE_PYTHON` to any torch+diffusers
  interpreter (e.g. assetFarm's venv) to skip the managed-runtime install.
  Model weights live in the STANDARD HuggingFace cache, so an existing cache
  is reused as-is. `NUCLEUS_IMAGE_PROVIDER=local` forces local generation
  everywhere (the old `assetfarm` value still works; `NUCLEUS_ASSETFARM_DIR`
  is gone — assetFarm is no longer used at runtime).

### Regions + deterministic compositing
The structured ops a UI — or a small planner model emitting JSON — drives
directly. No agent or code required.

- `GET /regions` — the open character's texture-region map: role → texture
  indexes (`fur`, `cloth`, `armor`, `eyes`, `face_detail`), `protected`
  indexes (eyes/mouth — skipped unless `force`), default `maskHints` per
  region, and per-index notes. Maps ship per character in
  `backend/assets/texture_regions/<Character>.json`; `approximate: true`
  flags a texture-count mismatch with the open DAT. 404 = no map (work with
  explicit textures + masks).
- `POST /composite` — re-fabric: lay a material over masked pixels, shaded by
  each texture's ORIGINAL lightness so folds/seams survive.
  `{region:"fur" | textures:[i...], material: {path}|{data:b64}|{generate:
  {prompt,...}}, mask?: {hueMin,hueMax,satMin,satMax,lumMin,lumMax},
  modulate?: {lo:0.3, hi:1.6}, force?}`. Mask defaults to the region's hint;
  hueMin>hueMax wraps through 0 (reds). Returns `{changed, skipped}`.
- `POST /hue-shift` — rotate hue / push saturation on masked pixels
  (lightness untouched): `{region|textures, mask?, hueShift?,
  saturationShift?, force?}`. Same targeting semantics as /composite.

Example — a whole themed skin in two calls (after /open):
```json
POST /composite {"region":"fur","material":{"generate":{"prompt":"molten lava"}},"modulate":{"lo":0.45,"hi":1.5}}
POST /hue-shift {"region":"cloth","hueShift":-160}
```

### Saving
- `GET /export-dat` — the edited DAT bytes (every pushed texture included).
- `POST /save {name}` — exports and saves to the vault as a NEW skin:
  - custom-character pseudo keys → that character's Custom Skins
    (`skins/add`), keeping the original `Pl*` dat name.
  - everything else → the unified intake (`/import/file`) with the original
    `Pl*` dat name (the intake only recognizes `Pl*`-stemmed DATs) and
    `custom_title` = your name. CSP/stock previews are auto-generated and
    slippi validation runs, exactly like a hand-imported skin.
  - intake dialogs (slippi-unsafe / duplicate) come back as the intake's own
    response payloads; pass `slippi_action` / `duplicate_action` through the
    save body to answer them.

## Gotchas

- The viewer streams JPEG frames continuously; the session throttles it to
  ~10 fps. `GET /frame` is the supported way to "see" — don't try to read the
  WebSocket yourself.
- Camera state is tracked backend-side by mirroring the protocol's delta math
  (the stream protocol has no absolute set). If something external moves the
  camera (nobody should), tracked state drifts.
- `GET /texture/<i>` returns the ORIGINAL from the DAT until you push an edit
  (the viewer caches its texture list at startup); the lab tracks edits and
  serves those back.
- Palette analyze on a freshly opened skin = originals at full resolution
  (better than the UI, which analyzes thumbnails).
- Eyes/details sharing a hue with clothes recolor together — same as the UI
  tool. For surgical edits, fetch the texture, edit pixels, push it back.
