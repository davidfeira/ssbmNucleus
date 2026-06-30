<!--
  GitHub release body for the NEXT release. release.bat reads this file verbatim
  as the GitHub Release notes. EDIT IT before each release (and bump the version
  in package.json). The short one-line note for the in-app updater is passed
  separately as release.bat's first argument. HTML comments like this are hidden
  on the rendered release page. Current content below is v0.4.3 (the last release)
  as a format reference.
-->
### 🐛 Fixes
- **Character-select portraits render imported costumes correctly.** Costumes whose
  eyes were drawn black/empty (Sonic, Wario and similar imports) now composite their
  eye textures properly, and replaced-model costumes no longer show low-poly geometry
  poking through. Regenerate CSPs to refresh existing portraits.
- **Costume accessories show up in portraits.** Attached hats and hair now sit on the
  model — e.g. Jigglypuff's nurse hat and the Falco-slot's long hair.
- **Pokémon Stadium custom stages no longer crash on boot** (caused by legacy
  alt-file extensions).
- **Reordering DAS stage variants no longer fails** with "Invalid fromIndex or
  toIndex" when an on-disk variant wasn't in the vault metadata.

### 🚀 Improvements
- **Fox and Falco's blaster renders as the real 3D model in portraits.**
- **Faster texture-pack exports.** HD portraits now render in parallel, sized to your
  machine's CPU, instead of one at a time.
- **Automatic Animelee detection** when organizing the vault.
- HD portraits are cached for bundle/patch exports, so repeat exports are instant.

### 🔧 Changes
- Stage and character names are hidden in the grids for a cleaner look.
- Bug-report zips no longer count Dolphin distribution files as Slippi logs.
- More robust Dolphin controller-pipe connection during in-game tests.
