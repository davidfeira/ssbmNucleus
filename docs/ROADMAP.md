# Nucleus Roadmap

**Goal**: Finish app features → App-website integration → Website refactor → Marketing → Monetization (Nucleus+ $6/month)

---

## PHASE 1: App Feature Completion

- [ ] Gun CSP preview (render gun model in HSD viewport like CSPs)
- [ ] Standardize buttons/toggles/modal styles and more sound polish


pages support in vault/install
better drag/drop - look into standard implementations
right click --> send to folder
---

## PHASE 1.5: Code Cleanup

**Large File Refactoring**

| File | Lines | Notes |
|------|-------|-------|
| `backend/mex_api.py` | 7,871 | Split into modules by feature area |
| `viewer/src/components/SkinCreator.jsx` | 2,023 | Extract sub-components |
| `viewer/src/components/mex/CharacterMode.jsx` | 1,612 | Extract sub-components |
| `viewer/src/components/storage/ExtrasPageView.jsx` | 1,228 | Extract sub-components |
| `viewer/src/components/StorageViewer.jsx` | 1,017 | Extract sub-components |

**Bug Fixes**
- [ ] Fix Ice Climbers
    - Write extensive ICs docs about the special things with them
    - Find all places where this could cause problems
    - Fix
- [ ] Fix Kirby
    - Write Kirby docs
    - Find where it could cause problems (probably just during installation - figure out Kirby hats)
  Fix Red Falcon .usd bugs
- [ ] Fix console errors
- [ ] Fix xdelta constant server connection for progress updates
- [ ] Fix HD CSP shadows and Ness/Fox bugs

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

- Texture pack export: use temp project copy instead of backup/restore (cleaner, avoids issues if export is interrupted)
- Stable diffusion stocks (AI-generated stock icons)
- AI rigger (auto-rig custom models)
- Custom stages
- SSS editor (stage select screen)
- Other texture mods (CSS, SSS, menus)
- 3D model viewer in CSP Studio
- Open skin in HSDRaw (check for new version)
- Open build in MEX Tool (use built-in version)
- Custom characters
- Code mods
- Music and sounds
- Replay viewer and clipper
- Automate texture pack offset names (analyze ISO hex or find MEX/HSD correlation)
- Show storage statistics (temp data size, ISO sizes)

