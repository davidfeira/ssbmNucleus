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
 *   node run-modded-match.js --closed-loop --stage fd   # memory-feedback char
 *                                            # + stage selection (default BF)
 */

const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const HERE = __dirname;
const BUILD = path.join(HERE, 'build-modded-iso.js');
const CONTROL = path.join(HERE, '..', 'dolphin', 'control.js');
const PIPE = path.join(HERE, '..', 'dolphin', 'pipe.js');
const OBSERVE = path.join(HERE, 'observe.py');
const CL_MATCH = path.join(HERE, 'cl_match.py');
const CL_DAS = path.join(HERE, 'cl_das.py');
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
  // A custom m-ex fighter is selectable in-match via its CSS icon coordinate
  // (manifest.cssIcon, the app's grid placement). costume mods select
  // fighter+costume. Anything else (stage mods, or a char build without an icon)
  // falls back to a boot-health crash-test (boot + reach the CSS so the mod's
  // data loads + watch process/frame health).
  const customChar = modType === 'character' && manifest.cssIcon && !flags.health;
  const customStage = modType === 'stage' && manifest.sssIcon && !flags.health;
  const customDas = modType === 'das' && manifest.dasVariants && !flags.health;
  const healthMode = !!flags.health || (modType !== 'costume' && !customChar && !customStage && !customDas);
  const stageFighter = (fighter && fighter !== true) ? fighter : 'fox';  // a vanilla pick to reach the SSS
  // Select a stage by its REAL coordinate from the build's SSS layout (accurate
  // on any layout); fall back to the libmelee-named target if not recorded.
  const stageArgsFor = (stage) => {
    const sl = manifest.stageLayout && manifest.stageLayout[stage];
    return sl ? ['--stage-icon', `${sl.page || 0},${sl.x},${sl.y}`] : [stage];
  };
  const label = (manifest.costumeId || manifest.characterName || manifest.stageName
    || (fighter ? `${fighter}-c${color}` : 'run')).replace(/[^a-z0-9_-]/gi, '-');

  if (!iso) throw new Error('no ISO to launch (run with --build or --iso, or build one first)');
  if (!fs.existsSync(iso)) throw new Error(`ISO not found: ${iso}`);
  if (!healthMode && !customChar && !customStage && !customDas && !fighter) throw new Error('no fighter to select (set --char or build a costume manifest)');
  log(`ISO: ${iso}`);
  if (healthMode) log(`mode: boot-health (modType=${modType}, ${label})`);
  else if (customStage) log(`mode: match — custom stage ${label} @page${manifest.sssIcon.page}(${manifest.sssIcon.x},${manifest.sssIcon.y})`);
  else if (customChar) log(`mode: match — select custom fighter ${label} @icon(${manifest.cssIcon.x},${manifest.cssIcon.y})`);
  else if (customDas) log(`mode: DAS stage skins — ${manifest.dasVariants.length} variant(s) on ${path.basename(iso)}`);
  else log(`mode: match — select ${fighter} costume ${color} (${label})`);

  // DAS special case: one ISO holds many stage skins (each legal stage can carry
  // several alternates, each behind a different HOLD button). Boot ONCE and test
  // every variant in a single session (cl_das.py): select the stage holding its
  // button, watch it load+run, then quit back to the CSS with L+R+A+START (which
  // keeps the fighter locked) and do the next -- no relaunch between skins.
  if (customDas) {
    const only = (flags.stage && flags.stage !== true) ? flags.stage : null;
    const variants = manifest.dasVariants.filter((v) => !only || v.stage === only);
    if (!variants.length) throw new Error(`no DAS variant for stage "${only}"`);
    log(`DAS: testing ${variants.length} stage skin(s) in one session (L+R+A+START reset between)`);
    try { node(CONTROL, ['kill']); } catch (e) { /* none */ }
    node(CONTROL, ['launch', '--iso', iso]);
    if (!waitForPipeReady(PIPE_READY_TIMEOUT_MS)) throw new Error('input pipe never appeared');
    sleepSync(MENU_WAIT_MS);
    node(PIPE, ['gotocss']);   // a CLEAN CSS (fighter NOT yet locked) -- cl_das locks it
    node(PIPE, ['cpustep']);
    const m = cp.spawnSync(VENV_PY, [CL_DAS, JSON.stringify(variants)], { stdio: 'inherit' });
    try { node(CONTROL, ['kill']); } catch (e) { /* none */ }
    process.exitCode = m.status === 0 ? 0 : 1;
    return;
  }

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
  } else if (customChar) {
    // Custom m-ex fighter: select it by its CSS icon coordinate (the app's grid
    // placement, recorded in the manifest), then stage + start -- one pipe.
    const stage = (flags.stage && flags.stage !== true) ? flags.stage : 'battlefield';
    const ic = manifest.cssIcon;
    log(`closed-loop: gotocss -> CPU -> cl_match ${label} @icon(${ic.x},${ic.y},${ic.index}) stage ${stage}`);
    node(PIPE, ['gotocss']);
    node(PIPE, ['cpustep']);
    const m = cp.spawnSync(VENV_PY,
      [CL_MATCH, label, '--icon', `${ic.x},${ic.y},${ic.index}`, ...stageArgsFor(stage)], { stdio: 'inherit' });
    if (m.status !== 0) throw new Error(`closed-loop custom-fighter select failed (${label})`);
    observeArgs = [OBSERVE, '--seconds', String(OBSERVE_SECONDS), '--label', label];
  } else if (customStage) {
    // Custom m-ex stage: pick a vanilla fighter to reach the SSS, then select
    // the custom stage by its SSS icon coordinate + page (R-switch to its page).
    const si = manifest.sssIcon;
    log(`closed-loop: gotocss -> CPU -> cl_match ${stageFighter} -> custom stage @page${si.page}(${si.x},${si.y})`);
    node(PIPE, ['gotocss']);
    node(PIPE, ['cpustep']);
    const m = cp.spawnSync(VENV_PY,
      [CL_MATCH, stageFighter, '--stage-icon', `${si.page},${si.x},${si.y}`], { stdio: 'inherit' });
    if (m.status !== 0) throw new Error(`closed-loop custom-stage select failed (${label})`);
    observeArgs = [OBSERVE, '--seconds', String(OBSERVE_SECONDS), '--label', label];
  } else if (flags['closed-loop']) {
    // Robust path: discrete per-frame steps to reach the CSS + add a CPU
    // (gotocss, cpustep), then a SINGLE memory-feedback process (cl_match.py)
    // that locks the character, advances to stage select, and picks the stage --
    // all on one persistent pipe. Splitting char- and stage-select into two
    // processes raced the character lock across the connection handoff (the
    // lock flag needs ~0.4s to settle); one pipe avoids that entirely.
    const stage = (flags.stage && flags.stage !== true) ? flags.stage : 'battlefield';
    log(`closed-loop: gotocss -> CPU -> cl_match ${fighter} c${color} stage ${stage}`);
    node(PIPE, ['gotocss']);
    node(PIPE, ['cpustep']);
    const m = cp.spawnSync(VENV_PY, [CL_MATCH, fighter, String(color), ...stageArgsFor(stage)], { stdio: 'inherit' });
    if (m.status !== 0) throw new Error(`closed-loop match setup failed (${fighter}/${stage})`);
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
