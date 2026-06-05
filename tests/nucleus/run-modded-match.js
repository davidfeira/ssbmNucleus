#!/usr/bin/env node

/*
 * run-modded-match.js -- end-to-end mod crash-test orchestrator.
 *
 * Ties the two harnesses together:
 *   1. (optional) build a modded ISO via build-modded-iso.js
 *   2. launch the modded ISO in Slippi Dolphin (tests/dolphin/control.js)
 *   3. drive the menus to start a match with the modded costume selected
 *      (tests/dolphin/pipe.js startmatch)
 *   4. screenshot the running match so you can see if the mod loaded or crashed
 *
 * It reads the build manifest (tests/artifacts/nucleus/last-build.json) for the
 * ISO path, fighter, and the modded costume's in-game color index.
 *
 * Usage:
 *   node run-modded-match.js                 # use the last build, run a match
 *   node run-modded-match.js --build         # build a fresh modded ISO first
 *   node run-modded-match.js --build --fighter Falco --costume <id>
 *   node run-modded-match.js --iso <path> --char Fox --color 4
 *   node run-modded-match.js --no-cpu        # 1-player (no CPU opponent)
 */

const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const HERE = __dirname;
const BUILD = path.join(HERE, 'build-modded-iso.js');
const CONTROL = path.join(HERE, '..', 'dolphin', 'control.js');
const PIPE = path.join(HERE, '..', 'dolphin', 'pipe.js');
const OBSERVE = path.join(HERE, 'observe.py');
const CL_SELECT = path.join(HERE, 'cl_select.py');
const VENV_PY = path.join(HERE, 'melee_venv', 'Scripts', 'python.exe');
const MANIFEST = path.join(HERE, '..', 'artifacts', 'nucleus', 'last-build.json');
const PIPE_READY_TIMEOUT_MS = 45000; // wait this long for Dolphin's input pipe
const MENU_WAIT_MS = 13000;          // after the pipe is up, time to reach the menu
const OBSERVE_SECONDS = 25;          // watch the match this long for crashes/hangs

function log(msg) {
  // eslint-disable-next-line no-console
  console.log(`[match] ${msg}`);
}

function sleepSync(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function parseArgs(argv) {
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const t = argv[i];
    if (t.startsWith('--')) {
      const key = t.slice(2);
      const val = argv[i + 1];
      if (val === undefined || val.startsWith('--')) flags[key] = true;
      else { flags[key] = val; i += 1; }
    }
  }
  return flags;
}

// Run a sibling node script, inheriting stdio so its progress is visible.
function node(script, args, opts) {
  const res = cp.spawnSync(process.execPath, [script, ...args], {
    stdio: 'inherit',
    ...opts,
  });
  if (res.status !== 0) {
    throw new Error(`${path.basename(script)} ${args.join(' ')} exited ${res.status}`);
  }
}

// Dolphin only creates \\.\pipe\slippibot1 once its input plugin initialises
// (≈ when the game starts booting), so a fixed boot sleep races it. Probe the
// pipe with a no-op `neutral` until it succeeds, confirming Dolphin is up.
function waitForPipeReady(timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = cp.spawnSync(process.execPath, [PIPE, 'neutral'], { stdio: 'ignore' });
    if (res.status === 0) return true;
    sleepSync(800);
  }
  return false;
}

function main() {
  const flags = parseArgs(process.argv.slice(2));

  // 1. Build (optional) -------------------------------------------------------
  if (flags.build) {
    const buildArgs = [];
    for (const k of ['type', 'mod', 'iso', 'fighter', 'costume', 'name']) {
      if (flags[k] && flags[k] !== true) buildArgs.push(`--${k}`, flags[k]);
    }
    log(`building a fresh modded ISO: build-modded-iso.js ${buildArgs.join(' ')}`);
    node(BUILD, buildArgs);
  }

  // 2. Resolve what to launch + select ---------------------------------------
  let manifest = {};
  if (fs.existsSync(MANIFEST)) {
    manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  }
  const iso = (flags.iso && flags.iso !== true) ? flags.iso : manifest.iso;
  const modType = manifest.modType || 'costume';
  const fighter = (flags.char && flags.char !== true) ? flags.char : manifest.fighter;
  let color = flags.color !== undefined && flags.color !== true
    ? parseInt(flags.color, 10)
    : manifest.colorIndex;
  if (color === undefined || color === null) {
    color = manifest.costumeCount ? manifest.costumeCount - 1 : 0;
  }
  // costume mods get a full match (select fighter+costume); other types can't be
  // auto-selected yet, so they fall back to a boot-health crash-test (boot +
  // reach the CSS so the mod's data loads + watch process/frame health).
  const healthMode = !!flags.health || modType !== 'costume';
  const label = (manifest.costumeId || manifest.characterName || manifest.stageName
    || (fighter ? `${fighter}-c${color}` : 'run')).replace(/[^a-z0-9_-]/gi, '-');

  if (!iso) throw new Error('no ISO to launch (run with --build or --iso, or build one first)');
  if (!fs.existsSync(iso)) throw new Error(`ISO not found: ${iso}`);
  if (!healthMode && !fighter) throw new Error('no fighter to select (set --char or build a costume manifest)');
  log(`ISO: ${iso}`);
  log(healthMode ? `mode: boot-health (modType=${modType}, ${label})`
    : `mode: match — select ${fighter} costume ${color} (${label})`);

  // 3. Launch -----------------------------------------------------------------
  log('killing any running Dolphin');
  try { node(CONTROL, ['kill']); } catch (e) { /* none running */ }
  log('launching modded ISO');
  node(CONTROL, ['launch', '--iso', iso]);
  log('waiting for Dolphin input pipe to come up...');
  if (!waitForPipeReady(PIPE_READY_TIMEOUT_MS)) {
    throw new Error('Dolphin input pipe never appeared (slippibot1); launch may have failed');
  }
  log(`pipe up; waiting ${MENU_WAIT_MS / 1000}s for the menu`);
  sleepSync(MENU_WAIT_MS);

  // 4. Drive the menus + 5. observe ------------------------------------------
  let observeArgs;
  if (healthMode) {
    log('navigating to the CSS so the mod loads, then watching boot health...');
    node(PIPE, ['gotocss']);
    observeArgs = [OBSERVE, '--health', '--seconds', String(OBSERVE_SECONDS), '--label', label];
  } else if (flags['closed-loop']) {
    // Robust path: discrete steps (nav + CPU + start) via the per-frame pipe,
    // analog character positioning via memory feedback (cl_select.py). The
    // selector is a separate process so its persistent pipe opens after the
    // node per-frame connections have closed.
    log('closed-loop: gotocss -> CPU -> memory-feedback select -> start');
    node(PIPE, ['gotocss']);
    node(PIPE, ['cpustep']);
    const sel = cp.spawnSync(VENV_PY, [CL_SELECT, fighter, String(color)], { stdio: 'inherit' });
    if (sel.status !== 0) throw new Error('closed-loop select did not lock the character');
    node(PIPE, ['poststart']);
    observeArgs = [OBSERVE, '--seconds', String(OBSERVE_SECONDS), '--label', label];
  } else {
    const smArgs = ['startmatch', fighter, '--color', String(color)];
    if (flags['no-cpu']) smArgs.push('--nocpu');
    log(`pipe.js ${smArgs.join(' ')}`);
    node(PIPE, smArgs);
    observeArgs = [OBSERVE, '--seconds', String(OBSERVE_SECONDS), '--label', label];
  }
  log(`observing for ${OBSERVE_SECONDS}s (${label})...`);
  const res = cp.spawnSync(VENV_PY, observeArgs, { stdio: 'inherit' });
  node(CONTROL, ['shot', '--label', 'modded-verify']);
  if (res.status === 0) {
    log(`PASS: ${label} loaded and ran without crash/hang.`);
  } else {
    log(`FAIL: ${label} crashed/hung/ended early — see crash-reports/.`);
    process.exitCode = 1;
  }
}

try {
  main();
} catch (err) {
  // eslint-disable-next-line no-console
  console.error(`[match] ERROR: ${err.message}`);
  process.exit(1);
}
