#!/usr/bin/env node

/*
 * build-modded-iso.js -- SSBM Nucleus build harness.
 *
 * Drives the Nucleus Flask backend's REST API (the same engine the desktop
 * app's UI calls) to produce a playable, modded Melee ISO end to end:
 *
 *   1. create a fresh project from a vanilla 1.02 ISO
 *   2. install a mod from the storage vault into that project, by --type:
 *        costume   -> POST /api/mex/import        (a fighter costume slot)
 *        character -> POST /custom-characters/install (a new m-ex roster slot)
 *        stage     -> POST /custom-stages/install  (a new stage)
 *   3. export a playable ISO
 *
 * It emits a manifest { iso, modType, ... } describing how to trigger the mod
 * in-game, so the match harness (run-modded-match.js) can boot, select it, and
 * observe for crashes.
 *
 * The backend runs standalone in DEV mode (venv Python, no Electron) and is
 * fully isolated from the installed app: dev mode roots all data in the repo
 * (projects/, storage/, output/), the app uses %LOCALAPPDATA%\SSBM Nucleus.
 *
 * Usage:
 *   node build-modded-iso.js [options]
 *     --type <kind>      costume | character | stage (default: costume)
 *     --mod <id>         specific vault item: costume id, or character/stage
 *                        slug or name (default: first slippi-safe of the type)
 *     --fighter <name>   for --type costume: which character (default: Fox)
 *     --iso <path>       vanilla 1.02 ISO to build from (default: working ISO)
 *     --name <project>   project name (default: harness-test)
 *     --backend <url>    use an already-running backend instead of spawning one
 *     --keep-backend     do not shut down a spawned backend on exit
 *     --keep-project     do not delete a pre-existing project dir first
 */

const net = require('net');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const VENV_PYTHON = path.join(REPO_ROOT, 'venv', 'Scripts', 'python.exe');
const STORAGE_DIR = path.join(REPO_ROOT, 'storage');
const OUTPUT_DIR = path.join(REPO_ROOT, 'output');
const PROJECTS_DIR = path.join(REPO_ROOT, 'projects');
const ARTIFACTS_DIR = path.join(REPO_ROOT, 'tests', 'artifacts', 'nucleus');
const DEFAULT_ISO = 'C:\\Users\\david\\projects\\melee\\working\\melee-vanilla-v1.02-working.iso';

function log(msg) {
  // eslint-disable-next-line no-console
  console.log(`[build] ${msg}`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseArgs(argv) {
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const t = argv[i];
    if (t.startsWith('--')) {
      const key = t.slice(2);
      const val = argv[i + 1];
      if (val === undefined || val.startsWith('--')) {
        flags[key] = true;
      } else {
        flags[key] = val;
        i += 1;
      }
    }
  }
  return flags;
}

// --- HTTP -------------------------------------------------------------------

async function api(baseUrl, method, route, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${baseUrl}${route}`, opts);
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error(`${method} ${route} -> ${res.status}, non-JSON: ${text.slice(0, 300)}`);
  }
  return { status: res.status, json };
}

// --- Backend lifecycle ------------------------------------------------------

// Spawn the dev backend, capture its output, resolve once it prints its port.
function spawnBackend() {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(VENV_PYTHON)) {
      reject(new Error(`venv python not found at ${VENV_PYTHON}`));
      return;
    }
    log('starting dev backend (venv python _run_backend.py)...');
    // _run_backend.py presents a fake-TTY stdin so flask-socketio's dev-server
    // guard (which aborts when stdin isn't a TTY -- the case under a Node spawn)
    // is satisfied, then runs the real mex_api.py unchanged.
    const launcher = path.join(__dirname, '_run_backend.py');
    const proc = spawn(VENV_PYTHON, [launcher], {
      cwd: REPO_ROOT,
      windowsHide: true,
    });
    const tail = [];
    let port = null;
    const onData = (chunk) => {
      const s = chunk.toString();
      for (const line of s.split(/\r?\n/)) {
        if (!line.trim()) continue;
        tail.push(line);
        if (tail.length > 80) tail.shift();
        const m = line.match(/BACKEND_PORT:(\d+)/);
        if (m && !port) {
          port = parseInt(m[1], 10);
          resolve({ proc, port, tail });
        }
      }
    };
    proc.stdout.on('data', onData);
    proc.stderr.on('data', onData);
    proc.on('error', reject);
    proc.on('exit', (code) => {
      if (!port) reject(new Error(`backend exited (code ${code}) before reporting a port:\n${tail.join('\n')}`));
    });
    setTimeout(() => {
      if (!port) reject(new Error(`backend did not report a port within 30s:\n${tail.join('\n')}`));
    }, 30000);
  });
}

async function waitForReady(baseUrl, tail) {
  let lastErr = 'no response';
  for (let i = 0; i < 120; i += 1) {
    try {
      const { json } = await api(baseUrl, 'GET', '/api/mex/status');
      if (json && json.connected) return json;
      lastErr = JSON.stringify(json);
    } catch (e) { lastErr = e.message; }
    await sleep(500);
  }
  const tailTxt = tail && tail.length ? `\n--- backend output ---\n${tail.join('\n')}` : '';
  throw new Error(`backend never became ready (/api/mex/status); last: ${lastErr}${tailTxt}`);
}

// --- Vault costume selection ------------------------------------------------

// Pick a slippi-safe costume for the fighter from the storage vault metadata.
function pickCostume(fighter, wanted) {
  const metaPath = path.join(STORAGE_DIR, 'metadata.json');
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const entry = (meta.characters || {})[fighter];
  const skins = entry && Array.isArray(entry.skins) ? entry.skins : [];
  if (!skins.length) throw new Error(`no vault costumes found for "${fighter}" in metadata.json`);

  let skin;
  if (wanted) {
    skin = skins.find((s) => s.id === wanted || s.filename === wanted || s.filename === `${wanted}.zip`);
    if (!skin) throw new Error(`requested costume "${wanted}" not found for ${fighter}`);
  } else {
    skin = skins.find((s) => s.slippi_safe && s.filename) || skins.find((s) => s.filename);
  }
  if (!skin || !skin.filename) throw new Error(`no usable costume for ${fighter}`);

  const diskPath = path.join(STORAGE_DIR, fighter, skin.filename);
  if (!fs.existsSync(diskPath)) throw new Error(`costume zip missing on disk: ${diskPath}`);
  // The /import endpoint resolves costumePath against the backend PROJECT_ROOT
  // (the repo root in dev), so a repo-relative POSIX-ish path is what it wants.
  const costumePath = `storage/${fighter}/${skin.filename}`;
  return { skin, costumePath };
}

// Pick a slug-based vault item (custom_characters / custom_stages) from
// metadata.json: the requested one by slug/name, else the first slippi-safe.
function pickFromMeta(key, wanted) {
  const meta = JSON.parse(fs.readFileSync(path.join(STORAGE_DIR, 'metadata.json'), 'utf8'));
  const list = meta[key] || [];
  if (!list.length) throw new Error(`no ${key} in vault metadata.json`);
  let item;
  if (wanted) {
    const w = String(wanted).toLowerCase();
    item = list.find((x) => x.slug === wanted || (x.name || '').toLowerCase() === w);
    if (!item) throw new Error(`requested ${key} "${wanted}" not found`);
  } else {
    item = list.find((x) => x.slippi_safe !== false) || list[0];
  }
  return item;
}

// --- CSS icon placement for custom fighters ---------------------------------

// m-ex's add-fighter leaves a new fighter's CSS icon at the default (0,0,0),
// which sits BELOW the roster grid in the port-panel zone -- so in-game the
// cursor can't hover+lock it (pressing A there toggles a port instead). This
// mirrors the app's "add it into the grid" step: move the new icon into a free
// roster slot (an empty bottom-row edge cell, which maps to a clean, lockable
// cursor position). Returns { x, y, index }: the icon's grid coordinate (the
// cursor target is (x, y - 3.5), validated) and its list index (== the in-game
// CSS grid index, used to confirm the hover).
async function placeCustomFighterIcon(baseUrl, fighterName) {
  const got = await api(baseUrl, 'GET', '/api/mex/menus/css/layout');
  const layout = got.json || {};
  const icons = layout.icons || [];
  if (!icons.length) throw new Error('css layout returned no icons');
  // The new fighter's icon: by name, else the unplaced one at (0,0), else last.
  let idx = icons.findIndex((ic) => (ic.fighterName || '') === fighterName);
  if (idx < 0) idx = icons.findIndex((ic) => Math.round(ic.x) === 0 && Math.round(ic.y) === 0);
  if (idx < 0) idx = icons.length - 1;
  // Free roster slots: the bottom row's empty edge cells (x = +/-28, y = 2),
  // which sit clear of the port panels; fall back to the upper-row edges.
  const key = (x, y) => `${Math.round(x)},${Math.round(y)}`;
  const occupied = new Set(icons.map((ic, i) => (i === idx ? null : key(ic.x, ic.y))));
  const candidates = [
    { x: -28.15, y: 2.0, z: -1.0 }, { x: 28.25, y: 2.0, z: -1.0 },
    { x: -28.15, y: 9.2, z: -1.0 }, { x: 28.25, y: 9.2, z: -1.0 },
    { x: -28.15, y: 16.4, z: -1.0 }, { x: 28.25, y: 16.4, z: -1.0 },
  ];
  const slot = candidates.find((c) => !occupied.has(key(c.x, c.y))) || candidates[0];
  icons[idx] = { ...icons[idx], x: slot.x, y: slot.y, z: slot.z };
  const post = await api(baseUrl, 'POST', '/api/mex/menus/css/layout',
    { template: layout.template, icons });
  if (!post.json || !post.json.success) {
    throw new Error(`css layout save failed: ${JSON.stringify(post.json)}`);
  }
  return { x: slot.x, y: slot.y, index: idx };
}

// --- SSS icon placement for custom stages -----------------------------------

// m-ex's add-stage puts a custom stage on a NEW page (e.g. "Custom") at the
// default (0,0,0). In-game you reach that page by pressing R (the m-ex SSS
// page-switch). We keep the stage on its own page (matching the app) but move
// its icon to a clear, reachable coordinate so the cursor can land + select it.
// Returns { page, x, y }: the page index to R-switch to, and the stage-cursor
// target (SSS layout coords ~= the in-game stage cursor, validated on the
// bottom-row legal stages).
async function placeCustomStageIcon(baseUrl, stageName) {
  const got = await api(baseUrl, 'GET', '/api/mex/menus/sss/layout');
  const layout = got.json || {};
  const pages = layout.pages || [];
  if (!pages.length) throw new Error('sss layout returned no pages');
  const iconsOf = (pg) => pg.icons || pg.stageIcons || [];
  // Locate the custom stage icon (by name, else the unplaced one at 0,0 on a
  // non-main page).
  let found = null;
  for (let pi = 0; pi < pages.length; pi += 1) {
    const icons = iconsOf(pages[pi]);
    let ii = icons.findIndex((ic) => (ic.stageName || '') === stageName);
    if (ii < 0 && pi > 0) ii = icons.findIndex((ic) => Math.round(ic.x) === 0 && Math.round(ic.y) === 0);
    if (ii >= 0) { found = { pi, ii }; break; }
  }
  if (!found) throw new Error(`could not find custom stage icon for "${stageName}"`);
  // A clear, reachable spot: the bottom-row legal-stage position (page 0's
  // Battlefield slot) -- same screen coords on any page, easy for the cursor.
  const slot = { x: 1.3, y: -9.1, z: 0.0 };
  const icons = iconsOf(pages[found.pi]);
  icons[found.ii] = { ...icons[found.ii], x: slot.x, y: slot.y, z: slot.z };
  const post = await api(baseUrl, 'POST', '/api/mex/menus/sss/layout', { pages });
  if (!post.json || !post.json.success) {
    throw new Error(`sss layout save failed: ${JSON.stringify(post.json)}`);
  }
  return { page: found.pi, x: slot.x, y: slot.y };
}

// --- SSS layout query (accurate stage-cursor coords) ------------------------

// The in-game stage cursor ~= the SSS icon coordinate, but a build's SSS layout
// can differ from libmelee's hardcoded vanilla targets (esp. Yoshi's Story,
// Fountain, Stadium) -- so selecting by the hardcoded coord mis-hits the wrong
// stage. Read the build's REAL layout (the SSS analog of the CSS icon fix) and
// map the 6 legal stages to their actual (x, y, page).
const SSS_LEGAL_NAMES = {
  Battlefield: 'battlefield', 'Final Destination': 'finaldestination',
  'Dream Land N64': 'dreamland', "Yoshi's Story": 'yoshisstory',
  'Pokemon Stadium': 'pokemonstadium', 'Fountain of Dreams': 'fountainofdreams',
};

async function queryStageLayout(baseUrl) {
  const got = await api(baseUrl, 'GET', '/api/mex/menus/sss/layout');
  const pages = (got.json && got.json.pages) || [];
  const layout = {};
  pages.forEach((pg, pi) => {
    for (const ic of (pg.icons || pg.stageIcons || [])) {
      const key = SSS_LEGAL_NAMES[ic.stageName];
      if (key && layout[key] === undefined) layout[key] = { x: ic.x, y: ic.y, page: pi };
    }
  });
  return layout;
}

// --- Export wait ------------------------------------------------------------

// The export runs in a background thread and only reports done over SocketIO,
// which we don't speak. Instead poll the output file: a finished Melee ISO is
// ~1.4 GB, so "exists, > 0.8 GB, and size unchanged across two checks" is a
// reliable completion signal. Surface backend output on timeout.
async function waitForIso(isoPath, backendTail) {
  const MIN_BYTES = 800 * 1024 * 1024;
  const TIMEOUT_MS = 6 * 60 * 1000;
  const start = Date.now();
  let lastSize = -1;
  let stableSize = -1;
  while (Date.now() - start < TIMEOUT_MS) {
    await sleep(3000);
    let size = 0;
    try {
      size = fs.statSync(isoPath).size;
    } catch (e) {
      log('  ...waiting for ISO to appear');
      continue;
    }
    const mb = (size / 1024 / 1024).toFixed(0);
    if (size === lastSize && size >= MIN_BYTES) {
      if (size === stableSize) {
        log(`  ISO stable at ${mb} MB`);
        return size;
      }
      stableSize = size;
      log(`  ISO ${mb} MB (confirming stable)`);
    } else {
      log(`  ISO ${mb} MB (growing)`);
      stableSize = -1;
    }
    lastSize = size;
  }
  const tailTxt = backendTail ? `\n--- backend tail ---\n${backendTail.join('\n')}` : '';
  throw new Error(`export timed out after ${TIMEOUT_MS / 1000}s waiting for ${isoPath}${tailTxt}`);
}

// --- Main flow --------------------------------------------------------------

async function main() {
  const flags = parseArgs(process.argv.slice(2));
  const isoPath = flags.iso || DEFAULT_ISO;
  const fighter = flags.fighter || 'Fox';
  const projectName = flags.name || 'harness-test';
  const modType = (flags.type && flags.type !== true) ? flags.type : 'costume';
  // The specific mod to install: costume id (for costume), or slug/name (for
  // custom-character/custom-stage). --costume kept as an alias for back-compat.
  const wantedTarget = [flags.mod, flags.costume, flags.target].find((v) => v && v !== true) || null;

  if (!fs.existsSync(isoPath)) throw new Error(`vanilla ISO not found: ${isoPath}`);

  // 1. Backend ---------------------------------------------------------------
  let backend = null;
  let baseUrl;
  if (flags.backend && flags.backend !== true) {
    baseUrl = flags.backend.replace(/\/$/, '');
    log(`using existing backend at ${baseUrl}`);
  } else {
    backend = await spawnBackend();
    baseUrl = `http://127.0.0.1:${backend.port}`;
    log(`backend on ${baseUrl}`);
  }

  const cleanup = async () => {
    if (backend && !flags['keep-backend']) {
      log('shutting down spawned backend');
      try { backend.proc.kill(); } catch (e) { /* ignore */ }
    }
  };

  try {
    await waitForReady(baseUrl, backend && backend.tail);

    const setup = await api(baseUrl, 'GET', '/api/mex/setup/status');
    if (!setup.json.complete) {
      throw new Error(`backend setup not complete: ${JSON.stringify(setup.json)}`);
    }
    log('setup complete; backend ready');

    // 2. Create project ------------------------------------------------------
    const projDir = path.join(PROJECTS_DIR, projectName);
    if (fs.existsSync(projDir) && !flags['keep-project']) {
      log(`removing existing project dir ${projDir}`);
      fs.rmSync(projDir, { recursive: true, force: true });
    }
    log(`creating project "${projectName}" from ${path.basename(isoPath)}`);
    const created = await api(baseUrl, 'POST', '/api/mex/project/create', {
      isoPath,
      projectName,
    });
    if (!created.json.success) throw new Error(`create failed: ${JSON.stringify(created.json)}`);
    log(`project created: ${created.json.projectDirectory}`);

    // create only writes the project; it does NOT load it into the MexManager.
    // The manager (needed by import/export) is loaded by an explicit open.
    const projectPath = created.json.projectPath;
    log(`opening project ${path.basename(projectPath)}`);
    const opened = await api(baseUrl, 'POST', '/api/mex/project/open', { projectPath });
    if (!opened.json.success) throw new Error(`open failed: ${JSON.stringify(opened.json)}`);

    // 3. Install the mod (routed by --type) ----------------------------------
    // modInfo carries the mod type + how to trigger it in-game (for the match
    // harness): costume -> {fighter, colorIndex}; character -> {characterName}
    // (a new roster slot); stage -> {stageName} (pick it on stage select).
    let modInfo;
    if (modType === 'costume') {
      const { skin, costumePath } = pickCostume(fighter, wantedTarget);
      log(`installing costume "${skin.id}" (${skin.costume_code}) onto ${fighter}`);
      const imported = await api(baseUrl, 'POST', '/api/mex/import', { fighter, costumePath });
      if (!imported.json.success) throw new Error(`import failed: ${JSON.stringify(imported.json)}`);
      // The import appends a costume slot -> it's the LAST entry, and that index
      // is the in-game X-cycle position (0 = default).
      const costumes = await api(baseUrl, 'GET', `/api/mex/fighters/${encodeURIComponent(fighter)}/costumes`);
      const list = (costumes.json && costumes.json.costumes) || [];
      const modCostume = list[list.length - 1] || {};
      const colorIndex = modCostume.index !== undefined ? modCostume.index : list.length - 1;
      log(`${fighter} now has ${list.length} costumes; mod at index ${colorIndex} (${modCostume.name || '?'})`);
      modInfo = { modType, fighter, colorIndex, costumeId: skin.id, costumeCode: skin.costume_code, costumeCount: list.length };
    } else if (modType === 'character') {
      const item = pickFromMeta('custom_characters', wantedTarget);
      log(`installing custom character "${item.name}" (${item.slug})`);
      const r = await api(baseUrl, 'POST', '/api/mex/custom-characters/install', { slug: item.slug });
      if (!r.json.success) throw new Error(`character install failed: ${JSON.stringify(r.json)}`);
      log(`added fighter "${item.name}" (${(r.json.costumeCount || item.costume_count || '?')} costumes)`);
      // Place its CSS icon into a real roster slot (add-fighter leaves it at
      // (0,0) in the port-panel zone, unselectable) -- the app's "add to grid".
      const cssIcon = await placeCustomFighterIcon(baseUrl, item.name);
      log(`placed ${item.name} CSS icon at grid slot (${cssIcon.x}, ${cssIcon.y}) [grid index ${cssIcon.index}]`);
      modInfo = { modType, characterName: item.name, characterSlug: item.slug, cssIcon };
    } else if (modType === 'stage') {
      const item = pickFromMeta('custom_stages', wantedTarget);
      log(`installing custom stage "${item.name}" (${item.slug})`);
      const r = await api(baseUrl, 'POST', '/api/mex/custom-stages/install', { slug: item.slug });
      if (!r.json.success) throw new Error(`stage install failed: ${JSON.stringify(r.json)}`);
      // Place its SSS icon onto page 0 at a free slot (add-stage puts it on a
      // separate "Custom" page at (0,0), which needs in-game page nav) so it's
      // selectable like a vanilla stage.
      const sssIcon = await placeCustomStageIcon(baseUrl, item.name);
      log(`placed stage "${item.name}" SSS icon at (${sssIcon.x}, ${sssIcon.y}) on page ${sssIcon.page}`);
      modInfo = { modType, stageName: item.name, stageSlug: item.slug, sssIcon };
    } else if (modType === 'das') {
      // Dynamic Alternate Stages: install the framework + one variant per legal
      // stage, each behind a HOLD button -- so ONE ISO crash-tests up to 6 stage
      // skins (hold the button on stage-select to load that stage's variant).
      const inst = await api(baseUrl, 'POST', '/api/mex/das/install', {});
      if (!inst.json.success) throw new Error(`das install failed: ${JSON.stringify(inst.json)}`);
      const meta = JSON.parse(fs.readFileSync(path.join(STORAGE_DIR, 'metadata.json'), 'utf8'));
      // stage code -> (vault folder, the name my stage selector uses)
      const DAS = {
        GrNBa: ['battlefield', 'battlefield'], GrNLa: ['final_destination', 'finaldestination'],
        GrSt: ['yoshis_story', 'yoshisstory'], GrOp: ['dreamland', 'dreamland'],
        GrPs: ['pokemon_stadium', 'pokemonstadium'], GrIz: ['fountain_of_dreams', 'fountainofdreams'],
      };
      // X/Y/Z have no stage-select function (A=select, B=back, R=m-ex page-
      // switch), so they're safe to HOLD while confirming the stage. Each stage
      // can carry several alternates -- one per button -- so --variants-per-stage
      // N installs N skins on each legal stage (N<=3). One ISO -> up to 18 skins.
      const BUTTONS = ['X', 'Y', 'Z'];
      const perStage = flags['variants-per-stage'] && flags['variants-per-stage'] !== true
        ? Math.min(parseInt(flags['variants-per-stage'], 10) || 1, BUTTONS.length) : 1;
      const only = (flags.stage && flags.stage !== true) ? flags.stage : null; // limit to one stage
      const dasVariants = [];
      for (const [code, [folder, selName]] of Object.entries(DAS)) {
        if (only && selName !== only) continue;
        const list = ((meta.stages || {})[folder] || {}).variants || [];
        // prefer slippi-safe, then fill with the rest; one variant per button
        const ordered = [...list].sort((a, b) => (b.slippi_safe ? 1 : 0) - (a.slippi_safe ? 1 : 0));
        const picks = ordered.slice(0, perStage);
        if (!picks.length) { log(`  no DAS variant in vault for ${folder}, skipping`); continue; }
        for (let k = 0; k < picks.length; k += 1) {
          const v = picks[k];
          const button = BUTTONS[k];
          const variantPath = `storage/das/${folder}/${v.filename}`;
          const imp = await api(baseUrl, 'POST', '/api/mex/das/import', { stageCode: code, variantPath });
          if (!imp.json.success) { log(`  das import failed (${folder}/${v.id}): ${JSON.stringify(imp.json)}`); continue; }
          const importedName = path.basename(imp.json.path || '', '.dat');
          const newName = `${importedName}(${button})`;
          const ren = await api(baseUrl, 'POST', '/api/mex/das/rename', { stageCode: code, oldName: importedName, newName });
          if (!ren.json.success) { log(`  das rename failed (${folder}/${v.id}): ${JSON.stringify(ren.json)}`); continue; }
          dasVariants.push({ stage: selName, stageCode: code, button, variant: v.name || v.id });
          log(`  DAS ${folder}: "${v.name || v.id}" -> hold ${button} on ${selName}`);
        }
      }
      if (!dasVariants.length) throw new Error('no DAS variants installed');
      // Attach each variant's REAL stage-cursor coordinate from the build's SSS
      // layout, so the selector lands on the right stage (not a libmelee guess).
      const stageLayout = await queryStageLayout(baseUrl);
      for (const v of dasVariants) {
        const sl = stageLayout[v.stage];
        if (sl) { v.x = sl.x; v.y = sl.y; v.page = sl.page; }
        else log(`  WARN: no SSS layout coord for ${v.stage}; will use vanilla target`);
      }
      modInfo = { modType, dasVariants, stageLayout };
    } else {
      throw new Error(`unknown --type "${modType}" (expected: costume | character | stage | das)`);
    }

    // Record the build's REAL stage-cursor coords for the 6 legal stages, so the
    // match harness selects stages accurately on any SSS layout (the SSS analog
    // of the CSS icon fix) -- not just for DAS.
    if (!modInfo.stageLayout) {
      modInfo.stageLayout = await queryStageLayout(baseUrl);
    }

    // 4. Export ISO ----------------------------------------------------------
    const comp = await api(baseUrl, 'GET', '/api/mex/recommended-compression');
    const ratio = (comp.json && comp.json.ratio) || 1.0;
    const isoName = `${projectName}.iso`;
    const outIso = path.join(OUTPUT_DIR, isoName);
    if (fs.existsSync(outIso)) fs.rmSync(outIso, { force: true });
    log(`exporting ISO "${isoName}" (cspCompression ${ratio})`);
    const exp = await api(baseUrl, 'POST', '/api/mex/export/start', {
      filename: isoName,
      cspCompression: ratio,
    });
    if (!exp.json.success) throw new Error(`export start failed: ${JSON.stringify(exp.json)}`);
    const finalBytes = await waitForIso(outIso, backend && backend.tail);
    log(`export complete: ${outIso} (${(finalBytes / 1024 / 1024).toFixed(0)} MB)`);

    // 5. Manifest ------------------------------------------------------------
    const manifest = {
      iso: outIso,
      ...modInfo,
      projectName,
      builtFrom: isoPath,
      bytes: finalBytes,
    };
    fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
    const manifestPath = path.join(ARTIFACTS_DIR, 'last-build.json');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    log(`manifest -> ${manifestPath}`);
    // eslint-disable-next-line no-console
    console.log(`\nMANIFEST ${JSON.stringify(manifest)}`);
  } finally {
    await cleanup();
  }
}

main().catch(async (err) => {
  // eslint-disable-next-line no-console
  console.error(`[build] ERROR: ${err.message}`);
  process.exit(1);
});
