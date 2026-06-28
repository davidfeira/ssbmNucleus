# SSBM Nucleus AI Modpack Duel Spec

This spec defines a fair head-to-head modpack challenge for two contestant
agents. The contestant agent is the creative director, planner, reviewer, and
operator. Nucleus provides execution tools: texture operations, local image
generation, project creation/editing, export, bundle packaging, and in-game
verification.

The short user prompt should be enough:

```text
Do the duel spec.
```

or:

```text
Do the duel spec in <theme or aesthetic>.
```

If no theme is supplied, the agent must choose a strong global creative
direction. If a theme is supplied, the agent should interpret it creatively and
cohesively across the whole pack.

Important: "AI theme" means the contestant agent's own creative direction. It
does not allow the banned built-in planner/reviewer endpoints listed below.

## Fresh Session Launcher

Use this section when starting a brand-new Codex or Claude session. The new
agent should not need prior chat context.

User prompt:

```text
Read docs/MODPACK_DUEL_SPEC.md and do the duel spec.
```

or, with a chosen aesthetic:

```text
Read docs/MODPACK_DUEL_SPEC.md and do the duel spec in <theme>.
```

Agent bootstrap requirements:

- Treat this document as the authoritative task definition.
- Inspect the repo before acting; do not rely on previous chat history.
- Use agent slug `codex` for Codex and `claude` for Claude unless the user says
  otherwise.
- Create all submission artifacts under `duel/<agent_slug>/`.
- If the user supplied `in <theme>`, use that theme. Otherwise choose a
  distinctive global theme yourself.
- Build through `tests/nucleus/build-duel-modpack.js` after the manifest
  validates.
- Stop and report a setup blocker if the local image provider or vanilla ISO is
  unavailable. Do not switch to remote generation or reduce required scope.

## Current Repo Support

The repo has enough infrastructure for the duel.

- Character editing:
  `docs/SKIN_LAB.md` and `backend/blueprints/skin_lab.py` expose
  `/api/mex/skin-lab/open`, `/regions`, `/composite`, `/tint`,
  `/hue-shift`, `/frame`, `/export-dat`, and `/save`.
- Local material generation:
  `/api/mex/skin-lab/generate-texture` routes through the vendored AI engine.
  Force local generation with `NUCLEUS_IMAGE_PROVIDER=local` and request
  `provider: "local"` in generated material payloads.
- Stage editing:
  `backend/skinlab/stage_ops.py` supports offline stage-region plans,
  texture replacement, material tinting, and DAS package generation. The
  stage-lab AI routes are reference implementations, not contestant planners.
- Region maps:
  `backend/assets/texture_regions/` contains maps for all required fighters
  plus Nana, and `backend/assets/texture_regions/stages/` contains maps for
  all six required legal stages.
- Project assembly:
  use `tests/nucleus/build-duel-modpack.js`. It validates a submitted manifest
  with `backend/duel_assembler.py`, then uses the existing app endpoints:
  `/api/mex/project/create`, `/project/open`, `/import-batch`,
  `/remove-batch`, `/das/install`, `/das/import`, `/das/rename`,
  `/export/start`, and `/bundle/export`.

The Python helper is validation and resolution glue only. It is not a planner
and it should not directly mutate projects for the submitted run.

## Non-Negotiable Rules

1. The contestant agent writes the plans and review decisions.
   Do not call `/api/mex/skin-lab/ai-create`,
   `/api/mex/stage-lab/ai-create`, or any OpenRouter planner/reviewer flow for
   final duel artifacts.

2. Use local picture generation for generated materials and backdrops.
   Set `NUCLEUS_IMAGE_PROVIDER=local` before running the backend, include
   `provider: "local"` in material generation requests, and record the local
   model ids used in the manifest. Do not silently fall back to remote image
   generation.

3. Use structured Nucleus operations unless a manual texture edit is documented:
   `composite`, `tint`, `hue-shift`, and stage `material-tint`.
   Raw binary edits are out of scope unless they go through existing Nucleus or
   HSDRawViewer tooling and are documented in the plan and manifest.

4. The final modpack must be playable from a clean NTSC 1.02 vanilla Melee ISO.
   The expected MD5 is `0e63d4223b01d9aba596259dc155a174`.

5. The final output must be reproducible from the submitted manifest and plans.

6. Generated content must remain in the Nucleus vault, and the editable Nucleus
   project must be preserved. The user should be able to open the project after
   the run, inspect installed costumes/stages, reorder or tweak content, and
   edit generated vault entries.

7. Do not use internet assets, remote inspiration scraping, or external image
   APIs for final duel artifacts. Work from the local repo, local models, and
   the agent-authored theme.

## Required Scope

### Character Coverage

Replace every vanilla visible costume slot for every playable character except
Mr. Game & Watch.

- Selectable fighters covered: 25.
- Visible vanilla slots covered: 119.
- Ice Climbers require Popo/Nana pairs for four slots.
- Total generated costume DATs when Nana pair files are counted: 123.

Use the canonical slot order in `backend/core/constants.py`:
`VANILLA_CSS_COLOR_ORDER`. Do not infer order from folder listings, vault order,
or filesystem order.

Excluded from selectable fighter coverage:

- `Mr. Game & Watch`
- Standalone `Nana`

Nana exists only as Ice Climbers pair data and must still have four generated
pair DATs.

### Legal Stage Coverage

Supply exactly one judged DAS skin for each legal stage, installed behind hold
button `X`. This DAS variant can be the only generated skin for that stage; for
judging, holding `X` is treated as loading the stage replacement.

The current endpoint harness accepts `mode: "das"` stage entries only. Do not
submit `default-replacement` stage entries unless this spec and harness are
explicitly updated.

| Stage | Code | Storage folder | Required mode | Button |
| --- | --- | --- | --- | --- |
| Battlefield | `GrNBa` | `battlefield` | `das` | `X` |
| Final Destination | `GrNLa` | `final_destination` | `das` | `X` |
| Yoshi's Story | `GrSt` | `yoshis_story` | `das` | `X` |
| Dream Land N64 | `GrOp` | `dreamland` | `das` | `X` |
| Pokemon Stadium | `GrPs` / `GrPs.usd` | `pokemon_stadium` | `das` | `X` |
| Fountain of Dreams | `GrIz` | `fountain_of_dreams` | `das` | `X` |

## Creative Requirements

Each agent chooses one global creative direction for the entire modpack, unless
the user supplied one with `in <theme>`. The final pack should read as one
designed release, not a random set of unrelated skins.

Global cohesion does not mean every fighter receives the same texture treatment.
The pack may share a visual language, but each fighter must have an intentional
design concept that fits that character's silhouette, readable features, and
available mapped regions. Each visible costume slot should also have a deliberate
palette, material placement, or accent variation. A slot should not be a copy of
another slot with only a different filename, display name, or automatic hue
shift.

Character skins should:

- Preserve silhouette and gameplay readability.
- Transform every major mapped region unless the theme explicitly benefits from
  preserving a stock feature.
- Include at least one clearly character-specific design hook, such as a
  distinctive material assignment, emblem treatment, armor/cloth language,
  accessory treatment, or palette relationship chosen for that fighter.
- Vary each visible costume slot intentionally. Team-color readability is a good
  reason for palette variation, but the plan should still describe why the slot
  belongs to the fighter and global theme.
- Avoid muddy low-contrast results and obvious stock-colored leftovers.
- Give small high-read regions such as eyes, cheeks, emblems, visors, gems, and
  face details deliberate treatment.
- Keep team-color readability where practical without making the result look
  like vanilla.

Stage skins should:

- Transform both playfield and background.
- Keep platforms, floor surfaces, ledges, and character contrast readable.
- Avoid backgrounds that visually swallow the playfield.
- Make the `X` DAS variant name clearly match the submitted theme.

### Material Reuse And Bespoke Design Standard

Efficient material reuse is allowed, but shared materials are only a library,
not the whole design. An agent may generate a local material library and reuse
those images across structured `composite` steps, as long as prompts, provider,
model ids, and reuse decisions are recorded in the plans.

It is not sufficient to apply the same small set of generated textures and
automatic tint or hue-shift rules across all fighters. Shared materials must be
combined with per-fighter and per-slot art direction: different region
assignments, accent colors, material priorities, protected details, fix steps,
or character-specific generated materials.

Good reuse examples:

- One global circuit material appears across the pack, but Mario uses it as
  jacket piping, Samus uses it as armor panel inlay, and Marth uses it as cape
  embroidery.
- A fighter family shares an archetype material, but each member gets distinct
  accent colors and mapped-region choices.
- A color slot uses the same base cloth as another slot, but has a planned
  team-color palette, different emblem treatment, and documented detail fixes.

Weak reuse examples:

- Every fighter uses the same three material images on the same broad region
  classes with only generic hue shifts.
- Plan files repeat the same review text for many slots without referencing the
  actual character, costume, preview, or fixes.
- Small high-read regions are left stock-colored because the shared material
  pass did not address them.

## Required Artifact Layout

Each agent submits under:

```text
duel/<agent_slug>/
  manifest.json
  plans/
    characters/<Character>/<CostumeCode>.json
    stages/<StageCode>.json
  previews/
    characters/<Character>/<CostumeCode>_review.jpg
    stages/<StageCode>_capture.png
  exports/
    final.iso
    final.ssbm
    optional_texture_pack/
  project/
    project_name.txt
```

Use stable agent slugs such as `codex` and `claude`.

## Manifest Contract

`manifest.json` is the source of truth for assembly. It must validate with:

```powershell
python backend/duel_assembler.py duel/<agent_slug>/manifest.json --dry-run --emit-harness-json
```

Top-level shape:

```json
{
  "agent": "codex-or-claude",
  "theme": "short global theme",
  "created_at": "ISO timestamp",
  "local_image_generation": {
    "required": true,
    "provider": "local",
    "models": ["model ids actually used"]
  },
  "characters": {},
  "ice_climbers_pairs": [],
  "stages": {},
  "build": {
    "projectName": "duel-codex",
    "sourceIsoMd5": "0e63d4223b01d9aba596259dc155a174",
    "nucleusProject": "projects/duel-codex/project.mexproj",
    "finalIso": "exports/final.iso",
    "bundle": "exports/final.ssbm"
  },
  "verification": {
    "bootHealth": "pass/fail/not_run",
    "stageCaptures": "pass/fail/not_run",
    "notes": []
  }
}
```

Each required character entry must be listed under its display name from
`VANILLA_CSS_COLOR_ORDER`:

```json
{
  "slot": 0,
  "costumeCode": "PlFxNr",
  "skinName": "display name",
  "vaultSkinId": "id after /api/mex/skin-lab/save",
  "plan": "plans/characters/Fox/PlFxNr.json",
  "preview": "previews/characters/Fox/PlFxNr_review.jpg"
}
```

Allowed vault resolvers for character entries:

- Preferred: `vaultSkinId`
- Accepted fallback: `filename`
- Accepted explicit path: `vaultPath` or `zipPath`

Ice Climbers pair entries must link each Popo slot to a Nana vault asset:

```json
{
  "slot": 0,
  "popoCode": "PlPpNr",
  "nanaCode": "PlNnNr",
  "popoVaultSkinId": "id matching the Ice Climbers character entry",
  "nanaVaultSkinId": "id"
}
```

Allowed Nana resolvers:

- Preferred: `nanaVaultSkinId`
- Accepted fallback: `nanaFilename`
- Accepted explicit path: `nanaVaultPath` or `nanaZipPath`

Each stage entry must use DAS mode:

```json
{
  "stage": "Battlefield",
  "skinName": "display name",
  "mode": "das",
  "button": "X",
  "vaultVariantId": "id",
  "plan": "plans/stages/GrNBa.json",
  "preview": "previews/stages/GrNBa_capture.png"
}
```

Allowed stage resolvers:

- Preferred: `vaultVariantId`
- Accepted fallback: `filename`
- Accepted explicit path: `variantPath`, `vaultPath`, or `zipPath`

## Plan File Contract

Each plan file should be the exact agent-authored plan that led to the final
asset, including review fixes. It does not need to include transient tool logs,
but it must be enough for another agent to understand and audit the result.

Character plan example:

```json
{
  "skin_name": "name",
  "theme_notes": "why this design fits the global theme",
  "design_intent": "what is specific to this fighter and costume slot",
  "source": {
    "character": "Fox",
    "costumeCode": "PlFxNr"
  },
  "material_reuse": {
    "shared_materials": ["global material ids used here"],
    "bespoke_choices": "why these regions, colors, and accents differ from other fighters or slots"
  },
  "steps": [
    {
      "op": "composite",
      "region": "cloth",
      "endpoint": "/api/mex/skin-lab/composite",
      "material_prompt": "seamless tileable local material prompt",
      "provider": "local",
      "model": "local model id",
      "mode": "project",
      "modulate": { "lo": 0.4, "hi": 1.6 }
    },
    {
      "op": "tint",
      "region": "emblem",
      "endpoint": "/api/mex/skin-lab/tint",
      "color": "#33f0ff",
      "strength": 0.8
    }
  ],
  "review": {
    "assessment": "agent-authored critique after seeing this specific render/capture",
    "fixes": [
      {
        "reason": "what looked weak, muddy, stock, or too similar",
        "steps_applied": []
      }
    ]
  }
}
```

Stage plan example:

```json
{
  "skin_name": "name",
  "stage": "Battlefield",
  "stageCode": "GrNBa",
  "mode": "das",
  "button": "X",
  "theme_notes": "why this stage fits the global theme",
  "design_intent": "what is specific to this stage layout and background",
  "steps": [
    {
      "op": "material-tint",
      "region": "main_platform",
      "material_prompt": "local generated material prompt",
      "provider": "local",
      "model": "local model id",
      "tint": "#33f0ff"
    }
  ],
  "review": {
    "assessment": "agent-authored critique after this specific in-game capture",
    "fixes": []
  }
}
```

## Recommended Workflow

1. Start the backend with local image generation forced:

```powershell
$env:NUCLEUS_IMAGE_PROVIDER = 'local'
npm run dev:backend
```

2. Preflight:

- `GET /api/mex/setup/status`
- `GET /api/mex/ai-engine/status`
- `GET /api/mex/ai-engine/models`
- Confirm required character and stage region maps exist.
- If local image generation is unavailable, stop and report the setup blocker.
  Do not fall back to remote generation.

3. Create the duel workspace:

```text
duel/<agent_slug>/
```

4. For each character slot:

- Open the vanilla costume with
  `POST /api/mex/skin-lab/open {"character":"Fox","costumeCode":"PlFxNr"}`.
- Read `GET /api/mex/skin-lab/regions`.
- Author a JSON plan from the region map and global theme.
- Write a fighter-specific `design_intent` before executing operations. It
  should name what makes this slot different from other fighters and other
  slots for the same fighter.
- Execute the plan through `/composite`, `/tint`, and `/hue-shift`.
- For generated materials, use local generation only. Prefer
  `mode: "project"` on body-scale composites.
- Capture review images with `/frame` or an existing review-sheet helper.
- Review the render yourself. If the result looks generic, too similar to other
  fighters, muddy, or stock in important regions, apply fix steps and record
  them in the plan.
- Save with `POST /api/mex/skin-lab/save {"name":"..."}`.
- Record the resulting vault skin id, plan path, and preview path in the
  manifest.

5. For Ice Climbers:

- Generate Popo assets through fighter `"Ice Climbers"`.
- Generate Nana assets through fighter `"Nana"` if supported by the local
  route stack, or through the existing Nana-capable storage/editing path.
- Do not merge Popo and Nana DATs into one project import zip.
- Record all four Popo/Nana pairs in `ice_climbers_pairs`.

6. For each legal stage:

- Author a stage plan from `backend/assets/texture_regions/stages/<Code>.json`.
- Use `backend/skinlab/stage_ops.py` or existing non-planner stage tooling to
  apply structured operations.
- Package the result as a DAS vault variant.
- Use `mode: "das"` and `button: "X"` in the manifest.
- Capture the stage in game while holding `X`.

7. Assemble the final project and exports:

```powershell
node tests\nucleus\build-duel-modpack.js duel\<agent_slug>\manifest.json --iso C:\path\to\GALE01.iso --force
```

Useful options:

- `--backend http://127.0.0.1:<port>` to reuse an existing backend.
- `--name duel-<agent_slug>` to force the project name.
- `--skip-artifact-checks` only for early manifest debugging, not final
  submission.
- `--no-bundle` only for debugging, not final submission.

The harness creates a fresh project, imports generated costumes in canonical
order, removes the original vanilla slots in descending order, installs DAS,
imports all six stage variants behind `X`, exports `final.iso`, exports
`final.ssbm`, updates build paths in the manifest, and preserves the project.

8. Verify:

- Boot-health test the final ISO.
- Capture all six legal stages with hold `X`.
- Spot-check representative costumes in game across light, dark, small, and
  high-detail fighters.
- Produce review sheets or review images for every generated visible costume
  slot.

## Final Acceptance Checklist

A submission is complete only if all items are true:

- `duel/<agent_slug>/manifest.json` exists and validates with
  `backend/duel_assembler.py`.
- Manifest covers 119 visible character slots in canonical order.
- Manifest covers four Nana pair assets, for 123 generated costume DATs total.
- Manifest excludes Mr. Game & Watch as a required fighter.
- All six legal stages are present as `mode: "das"` with `button: "X"`.
- Every character and stage entry resolves to an existing vault zip or explicit
  zip path.
- Every required plan file exists.
- Character plans record a slot-specific design intent and material reuse
  rationale. Repeated boilerplate is acceptable only for shared facts, not for
  the whole design or review.
- Preview/capture files exist, or any missing previews are explained in
  `verification.notes`.
- `exports/final.iso` exists.
- `exports/final.ssbm` exists.
- `project/project_name.txt` exists and names a preserved Nucleus project.
- `local_image_generation.provider` is `local`, with model ids recorded.
- Verification fields are updated after boot/stage testing.

## Scoring

Score out of 100:

- Coverage and correctness, 25: every required slot/stage present, correct slot
  order, Ice Climbers paired correctly, no Mr. Game & Watch requirement leak.
- Character visual quality, 25: clear theme execution, full-region coverage,
  bespoke per-fighter and per-slot design choices, polished materials, readable
  silhouettes and details.
- Stage visual quality, 15: transformed playfields/backgrounds, readable legal
  stages, strong `X` DAS captures.
- Cohesion, 15: the pack feels like one designed modpack rather than unrelated
  individual skins.
- Stability, 10: ISO boots, CSS/SSS function, sampled matches and stage loads
  do not crash or hang.
- Reproducibility, 10: manifest, plans, prompts, local model usage, and previews
  are complete enough to rebuild and audit.

Generic material-library submissions can be valid and reproducible, but should
lose points under Character visual quality and Cohesion when the same materials,
region choices, and review language are reused across most fighters without
clear per-character art direction.

Disqualifiers:

- Missing final ISO or manifest.
- Any remote/OpenRouter image generation used for final assets.
- Built-in AI planner/reviewer flow used instead of the contestant agent's own
  planning and review.
- Final ISO cannot reach CSS.
- Multiple missing fighters, missing Ice Climbers pair data, or missing legal
  stage skins.
- Stage submissions not installed as judged `X` DAS variants.

## Notes For Contestant Agents

Read this spec, then execute it. Do not ask the user to choose individual
fighters, colors, stages, or prompts unless the user explicitly wants to direct
the art. If the user says `in <theme>`, use that as the global aesthetic. If the
user does not provide a theme, choose one yourself and make it distinctive.

You are the planner and reviewer. Read region maps and rendered/captured images
yourself, author the JSON plans, apply fixes, and use Nucleus to execute the
operations. The goal is a complete, creative, editable modpack that another
agent or human can audit from the submitted manifest.
