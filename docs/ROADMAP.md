# Nucleus Roadmap

## Overview

**Goal**: Finish app features → App-website integration → Website refactor → Marketing → Monetization (Nucleus+ $6/month)

---

## PHASE 1: App Feature Completion

### Group A: Settings Page
- [x] Vanilla ISO path not saved during first-run setup
- [x] Discord link in settings
- [x] Settings page redesign (flat layout, wider)
- [x] Storage statistics (costumes, stages, extras, patches, vault size)

### Group B: Install Page UI
- [ ] Install UI redesign
- [x] Hide extras button for characters without extras
- [x] Show back button without needing to click an extra first

### Group C: Custom Poses (CSP Studio)
- [x] Custom poses don't load in HD regeneration mode
- [x] Wrong objects not being hidden

### Group G: Vault Organization
- [ ] Drag and drop improvements for skin reordering

### Group D: Build/Export Flow
- [x] Not deleting output ISO after download (startup cleanup + post-download cleanup)
- [ ] Texture pack mode not downscaling placeholder images (memory issue)

### Group E: External Tool Integration
- [ ] Open skin in HSDRaw (check for new version)
- [ ] Open build in MEX Tool (use built-in version)

### Group F: Polish
- [ ] Sounds (CSP tick noise, start button noise)

### Extras: Effects (PlXx.dat mods)
- [x] Fox/Falco effects
  - Laser
  - Shine
  - Side-B
  - Up-B
- [x] Marth/Roy/Link/Young Link sword swing trails

### Extras: Models (new type)
- [x] Fox/Falco gun model (custom .dae import via HSDRawViewer CLI)

### Already Done / Mostly Done
- [x] CSP Studio (pose manager, HD generation, alt CSPs)
- [x] Laser Editor
- [x] Extras system foundation
- [x] HD resolution options (2x, 3x, 4x)
- [x] All extra editor modals with delete functionality
- [x] Model extras type (gun imports)

---

## PHASE 1.5: Code Cleanup

Break down massive files to improve maintainability:

| File | Lines | Notes |
|------|-------|-------|
| `backend/mex_api.py` | 7,871 | Split into modules by feature area |
| `viewer/src/components/SkinCreator.jsx` | 2,023 | Extract sub-components |
| `viewer/src/components/mex/CharacterMode.jsx` | 1,612 | Extract sub-components |
| `viewer/src/components/storage/ExtrasPageView.jsx` | 1,228 | Extract sub-components |
| `viewer/src/components/StorageViewer.jsx` | 1,017 | Extract sub-components |

---

## PHASE 2: App-Website Integration

### Download Integration
- [ ] Browse mods from within app
- [ ] One-click download to storage
- [ ] Preview images/metadata before download
- [ ] Authentication for Nucleus+ subscribers

### Upload Integration (later priority)
- [ ] Upload skins directly from app
- [ ] Auto-generate CSP/thumbnails on upload
- [ ] Link to user's website account

---

## PHASE 3: Website Refactor

### Database Refactoring
- [ ] Review and fix schema issues
- [ ] Add support for new mod types (extras, effects, etc.)
- [ ] Think through relationships (skin → extras, modpacks)
- [ ] Migration plan for existing data

### Core Fixes
- [ ] Fix Slippi detect bug (install .NET?)
- [ ] Fix supabase alerts
- [ ] Fix posts display

### Features
- [ ] Discord embed preview (image + name)
- [ ] Full data control verification
- [ ] Comments & likes system
- [ ] Recent activity feed
- [ ] Hide duplicate mods
- [ ] Better user activity tracking

### Dev Pipeline
- [ ] Local DB for development (don't touch prod)
- [ ] Database backup capabilities
- [ ] Proper branches (don't push to prod until ready)

### Modpack Support (stretch)
- [ ] Better modpack organization
- [ ] Modpack creators can post updates

---

## PHASE 4: Legal & Release Prep

- [ ] Licenses / Credits documentation
- [ ] Change GitHub name / repo name
- [ ] Better README with:
  - Trailer video
  - Guide / tutorial
  - Feature overview

---

## PHASE 5: Marketing Campaign

- [ ] Create trailer video
- [ ] Write tweet copy (multiple variations)
- [ ] Reddit posts (r/ssbm, r/smashbros, etc.)
- [ ] Discord announcements
- [ ] YouTube tutorial/showcase
- [ ] Reach out to Melee content creators

---

## PHASE 6: Monetization

### Nucleus+ ($6/month)
- [ ] Payment integration (Stripe?)
- [ ] User subscription management
- [ ] Gated features:
  - In-app downloads
  - Priority/exclusive mods?
  - Cloud storage for builds?

---

## WAY LATER (Backlog)

These are cool ideas but not priority:

- Stable diffusion stocks (AI-generated stock icons)
- AI rigger (auto-rig custom models?)
- Custom stages
- SSS editor (stage select screen)
- Other texture mods (CSS, SSS, menus)
- 3D model viewer in CSP Studio
- Shareable poses / pose marketplace

---

## Current Status

**Last updated**: January 2026

**Currently working on**: Phase 1 - Group B (Install Page UI)

**Recent completions**:
- Install page: hide extras button when none available, always-visible back button
- Settings page: ISO path fix, Discord link, flat layout redesign, storage stats
- Output folder cleanup on startup (ISOs, mod exports, vault backups)
- Fox/Falco gun model import (custom .dae via HSDRawViewer CLI)
- Delete buttons on all editor modals
- Thunder/Shadow Ball/Sword trail editors
- Shine and Up-B color editors (shared Fox/Falco)
- HD resolution standardization (2x, 3x, 4x)
- Pose Manager CSP viewport fix
- Laser Editor implementation
- Extras system foundation
- CSP upload modal with Normal/HD slots
