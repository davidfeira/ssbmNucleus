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
      modInfo = { modType, characterName: item.name, characterSlug: item.slug };
    } else if (modType === 'stage') {
      const item = pickFromMeta('custom_stages', wantedTarget);
      log(`installing custom stage "${item.name}" (${item.slug})`);
      const r = await api(baseUrl, 'POST', '/api/mex/custom-stages/install', { slug: item.slug });
      if (!r.json.success) throw new Error(`stage install failed: ${JSON.stringify(r.json)}`);
      modInfo = { modType, stageName: item.name, stageSlug: item.slug };
    } else {
      throw new Error(`unknown --type "${modType}" (expected: costume | character | stage)`);
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
