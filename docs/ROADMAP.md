# Nucleus Roadmap

## Overview

**Goal**: Finish app features → App-website integration → Website refactor → Marketing → Monetization (Nucleus+ $6/month)

---

## PHASE 1: App Feature Completion

### Bugs / Polish
- [ ] Vanilla ISO path not saved during first-run setup (requires re-setting in Settings)
- [ ] Not deleting output ISO after download
- [ ] Custom poses not working properly:
  - Don't load in HD regeneration mode
  - Wrong objects not being hidden
- [ ] Drag and drop improvements
- [ ] Install UI redesign
- [ ] Fix vertex bug with Up-B edits for Fox/Falco
- [ ] Better icons/display/UI for extras page

### Extras: Effects (PlXx.dat mods)
- [x] Fox/Falco effects
  - Laser
  - Shine
  - Side-B
  - Up-B
- [x] Marth/Roy/Link/Young Link sword swing trails

### Extras: Models (new type)
- [x] Fox/Falco gun model (custom .dae import via HSDRawViewer CLI)
- [ ] Peach toad

### UX Additions
- [ ] Discord link in settings
- [ ] Sounds (CSP tick noise, start button noise)
- [ ] Open skin in HSDRaw (check for new version)
- [ ] Open build in MEX Tool (use built-in version for stability)

### Already Done / Mostly Done
- [x] CSP Studio (pose manager, HD generation, alt CSPs)
- [x] Laser Editor
- [x] Extras system foundation
- [x] HD resolution options (2x, 3x, 4x)
- [x] All extra editor modals with delete functionality
- [x] Model extras type (gun imports)

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

**Currently working on**: Phase 1 - UX additions

**Recent completions**:
- Fox/Falco gun model import (custom .dae via HSDRawViewer CLI)
- Delete buttons on all editor modals
- Thunder/Shadow Ball/Sword trail editors
- Shine and Up-B color editors (shared Fox/Falco)
- HD resolution standardization (2x, 3x, 4x)
- Pose Manager CSP viewport fix
- Laser Editor implementation
- Extras system foundation
- CSP upload modal with Normal/HD slots
