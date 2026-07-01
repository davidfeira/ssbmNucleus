# Documentation System

How documentation is organized in this repo, and the checklist for keeping it
current when things ship. If you are about to write something down and don't
know where it goes, start here.

## The Tiers

| Tier | Location | Audience | Contract |
|------|----------|----------|----------|
| **Wiki** | `wiki/*.md` | Users of the app | Polished, workflow-oriented, always current. No code paths, no endpoints. |
| **Evergreen dev docs** | `docs/` (see map below) | Developers / AI assistants | Kept current with the code. Wrong info here gets fixed, not tolerated. |
| **Research docs** | `docs/` + `docs/research/` | Developers | Point-in-time investigation write-ups. Valuable history, NOT maintained against the current code. |
| **Changelog** | `CHANGELOG.md` | Users | User-visible changes per release, under `## Unreleased` until shipped. |
| **Agent context** | `CLAUDE.md` + auto-memory | AI assistants | Hard-won gotchas and workflow rules only — not a mirror of the docs. |

## The Ship Checklist

When a change lands, update docs in the same change (not "later"):

1. **User-visible feature or behavior change** → edit or add a wiki page, and
   add a `CHANGELOG.md` entry. New wiki pages must be registered in **both**
   `wiki/wiki.js` (`NAV_SECTIONS`) and `wiki/README.md`.
2. **Endpoint added/changed/removed** → `docs/API_REFERENCE.md` (the Blueprint
   Summary table counts AND the endpoint section).
3. **New blueprint, backend module, or frontend hook** → the matching table in
   `docs/ARCHITECTURE.md`.
4. **Behavior a wiki page or dev doc describes changed** → fix the page in the
   same PR that changes the behavior. A stale doc is worse than no doc.
5. **Removed a feature or flow** → delete or rewrite its doc sections. Git
   history is the archive; the working tree should never describe things that
   no longer exist.

## Wiki Conventions

- Plain voice, second person, short sections. Describe what the app does and
  why it matters, not how the code does it.
- No file paths, endpoints, or module names — those belong in `docs/`.
- Every page links its related pages at the bottom.
- Preview locally with `npm run wiki` (or `open_wiki.bat`) at
  `http://127.0.0.1:4173/wiki/`.

## Dev Doc Conventions

- Research docs should say so up front (a one-liner like *"Investigation
  write-up (2026-06); describes the state at the time"*) so a reader knows not
  to treat them as current.
- Don't reference scratch scripts that won't be kept. If a one-off probe
  proved something, state the finding and note the probe was not kept.
- One doc per topic; extend the existing doc instead of starting
  `TOPIC_V2.md`.

## Docs Map

Evergreen (kept current):

- `ARCHITECTURE.md` — system overview: layers, blueprints, hooks, dirs
- `API_REFERENCE.md` — every Flask endpoint
- `DEVELOPMENT.md` — dev environment setup and running
- `DISTRIBUTION_GUIDE.md` / `LINUX_BUILD.md` — packaging and installers
- `ROADMAP.md` — feature roadmap, updated as phases complete
- `MELEE_MODDING.md` — Melee domain knowledge (DAT formats, character codes)
- `MENUS_SYSTEM.md` — CSS/SSS menu-mod backend
- `CUSTOM_CONTENT.md` — custom characters/stages, ISO scanning backend
- `INGAME_TESTING.md` — the `backend/ingame/` test engine
- `SKIN_LAB.md` — the Skin Lab REST surface (agent/scripting API)
- `VAULT_SQLITE_MIGRATION.md` — vault DB design (live during the migration)
- `DOCUMENTATION.md` — this file

Research / point-in-time (not maintained; check dates before trusting):

- `MEX_BUILD_LIMITS.md` — build-limit research + its probe-script toolkit
- `LOWPOLY_SHADOWS.md`, `CSP_LOWPOLY_HIDING.md`,
  `ANIMATION_PART_VISIBILITY.md` — rendering investigations (the findings
  shipped; the write-ups are history)
- `CSP_RENDERING_DEBUG.md` — CSP debugging workflow + past-bug casebook
- `IMPORT_INVENTORY.md` — import-surface stock-take from the unification work
- `MEX_INTEGRATION.md` — early MexCLI integration notes
- `CUSTOM_STAGES_SPEC.md`, `MODPACK_DUEL_SPEC.md` — design docs for their
  features (implementation may differ in details)
- `docs/research/`, `docs/iso-migration/` — raw reference material

## What NOT To Do

- Don't put user-facing how-tos in `docs/` — they rot invisibly there. If a
  user would want it, it's a wiki page.
- Don't duplicate content across tiers; link instead.
- Don't leave a doc describing removed behavior "for context" — rewrite it as
  explicitly historical or delete it.
