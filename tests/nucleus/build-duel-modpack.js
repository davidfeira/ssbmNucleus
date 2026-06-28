#!/usr/bin/env node

/*
 * build-duel-modpack.js -- endpoint-driven assembler for docs/MODPACK_DUEL_SPEC.md.
 *
 * This keeps project mutation on the same Flask routes the app and existing
 * harnesses use:
 *   project/create + project/open
 *   import-batch + remove-batch
 *   das/install + das/import + das/rename
 *   export/start
 *   bundle/export
 *
 * The Python helper only validates the duel manifest and resolves canonical
 * costume/stage work items; it does not plan or review content.
 *
 * Usage:
 *   node tests/nucleus/build-duel-modpack.js duel/codex/manifest.json --iso C:\path\GALE01.iso --force
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const HERE = __dirname;
const REPO_ROOT = path.resolve(HERE, '..', '..');
const VENV_PYTHON = path.join(REPO_ROOT, 'venv', 'Scripts', 'python.exe');
const PY_HELPER = path.join(REPO_ROOT, 'backend', 'duel_assembler.py');
const STORAGE_DIR = path.join(REPO_ROOT, 'storage');
const OUTPUT_DIR = path.join(REPO_ROOT, 'output');
const PROJECTS_DIR = path.join(REPO_ROOT, 'projects');
const ARTIFACTS_DIR = path.join(REPO_ROOT, 'tests', 'artifacts', 'nucleus');
const BACKEND_LOG = path.join(ARTIFACTS_DIR, 'duel-backend.log');
const VANILLA_MD5 = '0e63d4223b01d9aba596259dc155a174';

function log(msg) { console.log(`[duel] ${msg}`); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function parseArgs(argv) {
  const flags = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) {
      flags._.push(token);
      continue;
    }
    const key = token.slice(2);
    const val = argv[i + 1];
    if (val === undefined || val.startsWith('--')) flags[key] = true;
    else { flags[key] = val; i += 1; }
  }
  return flags;
}

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

function spawnBackend() {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(VENV_PYTHON)) {
      reject(new Error(`venv python not found at ${VENV_PYTHON}`));
      return;
    }
    fs.mkdirSync(path.dirname(BACKEND_LOG), { recursive: true });
    const logFd = fs.openSync(BACKEND_LOG, 'w');
    log(`starting dev backend with NUCLEUS_IMAGE_PROVIDER=local -> ${BACKEND_LOG}`);
    const proc = spawn(VENV_PYTHON, [path.join(HERE, '_run_backend.py')], {
      cwd: REPO_ROOT,
      windowsHide: true,
      stdio: ['ignore', logFd, logFd],
      env: { ...process.env, NUCLEUS_IMAGE_PROVIDER: 'local' },
    });
    proc.on('error', reject);
    let done = false;
    const deadline = Date.now() + 30000;
    const poll = setInterval(() => {
      let text = '';
      try { text = fs.readFileSync(BACKEND_LOG, 'utf8'); } catch (e) { /* not ready */ }
      const match = text.match(/BACKEND_PORT:(\d+)/);
      if (match && !done) {
        done = true;
        clearInterval(poll);
        resolve({ proc, port: parseInt(match[1], 10) });
      } else if (Date.now() > deadline && !done) {
        done = true;
        clearInterval(poll);
        reject(new Error(`backend did not report a port within 30s; see ${BACKEND_LOG}`));
      }
    }, 400);
    proc.on('exit', (code) => {
      if (!done) {
        done = true;
        clearInterval(poll);
        reject(new Error(`backend exited early with code ${code}; see ${BACKEND_LOG}`));
      }
    });
  });
}

async function waitForReady(baseUrl) {
  let last = 'no response';
  for (let i = 0; i < 120; i += 1) {
    try {
      const { json } = await api(baseUrl, 'GET', '/api/mex/status');
      if (json && json.connected) return json;
      last = JSON.stringify(json);
    } catch (e) {
      last = e.message;
    }
    await sleep(500);
  }
  throw new Error(`backend never became ready: ${last}`);
}

function resolveDuelWork(manifestPath, flags) {
  const python = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python';
  const args = [PY_HELPER, manifestPath, '--dry-run', '--emit-harness-json'];
  if (flags['skip-artifact-checks']) args.push('--skip-artifact-checks');
  const res = spawnSync(python, args, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    env: { ...process.env, NUCLEUS_IMAGE_PROVIDER: 'local' },
  });
  if (res.status !== 0) {
    throw new Error(`duel manifest validation failed:\n${res.stdout || ''}${res.stderr || ''}`);
  }
  const line = (res.stdout || '').split(/\r?\n/).find((s) => s.startsWith('HARNESS_JSON '));
  if (!line) {
    throw new Error(`duel helper did not emit HARNESS_JSON:\n${res.stdout}`);
  }
  return JSON.parse(line.slice('HARNESS_JSON '.length));
}

function safeProjectDir(projectName) {
  if (!projectName || /[\\/:*?"<>|]/.test(projectName)) {
    throw new Error(`invalid project name: ${projectName}`);
  }
  const dir = path.resolve(PROJECTS_DIR, projectName);
  const rel = path.relative(PROJECTS_DIR, dir);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    throw new Error(`project path escapes managed project root: ${dir}`);
  }
  return dir;
}

async function md5File(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('md5');
    const stream = fs.createReadStream(filePath);
    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('error', reject);
    stream.on('end', () => resolve(hash.digest('hex')));
  });
}

async function waitForStableFile(filePath, minBytes, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;
  let lastSize = -1;
  let stableSize = -1;
  while (Date.now() < deadline) {
    await sleep(3000);
    let size = 0;
    try { size = fs.statSync(filePath).size; } catch (e) { log(`waiting for ${label} to appear`); continue; }
    const mb = (size / 1024 / 1024).toFixed(0);
    if (size === lastSize && size >= minBytes) {
      if (size === stableSize) {
        log(`${label} stable at ${mb} MB`);
        return size;
      }
      stableSize = size;
      log(`${label} ${mb} MB; confirming stable`);
    } else {
      stableSize = -1;
      log(`${label} ${mb} MB; growing`);
    }
    lastSize = size;
  }
  throw new Error(`${label} timed out after ${Math.round(timeoutMs / 1000)}s: ${filePath}`);
}

async function waitForBundle(baseUrl, bundleId, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const { json } = await api(baseUrl, 'GET', '/api/mex/bundle/list');
      const bundle = (json.bundles || []).find((b) => b.id === bundleId);
      if (bundle && bundle.size > 0) return bundle;
    } catch (e) { /* retry */ }
    await sleep(2500);
  }
  return null;
}

function relFrom(base, target) {
  return path.relative(base, target).replace(/\\/g, '/');
}

function updateManifest(manifestPath, values) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.created_at = manifest.created_at || new Date().toISOString();
  manifest.build = {
    ...(manifest.build || {}),
    sourceIsoMd5: values.sourceIsoMd5,
    nucleusProject: relFrom(REPO_ROOT, values.projectPath),
    finalIso: relFrom(path.dirname(manifestPath), values.finalIso),
    bundle: values.finalBundle ? relFrom(path.dirname(manifestPath), values.finalBundle) : (manifest.build || {}).bundle,
  };
  manifest.verification = {
    bootHealth: (manifest.verification || {}).bootHealth || 'not_run',
    stageCaptures: (manifest.verification || {}).stageCaptures || 'not_run',
    notes: (manifest.verification || {}).notes || [],
  };
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
}

async function main() {
  const flags = parseArgs(process.argv.slice(2));
  const manifestArg = flags._[0] || flags.manifest;
  if (!manifestArg) throw new Error('usage: build-duel-modpack.js <manifest.json> --iso <vanilla.iso>');
  const isoArg = flags.iso || flags['vanilla-iso'];
  if (!isoArg || isoArg === true) throw new Error('usage: build-duel-modpack.js <manifest.json> --iso <vanilla.iso>');
  const manifestPath = path.resolve(REPO_ROOT, manifestArg);
  const vanillaIso = path.resolve(isoArg);
  if (!fs.existsSync(manifestPath)) throw new Error(`manifest not found: ${manifestPath}`);
  if (!fs.existsSync(vanillaIso)) throw new Error(`vanilla ISO not found: ${vanillaIso}`);

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const work = resolveDuelWork(manifestPath, flags);
  log(`validated ${work.visibleSlots} visible slots, ${work.generatedCostumeDats} generated costume DATs`);
  log(`resolved ${work.importItems.length} costume imports, ${work.removeItems.length} removals, ${work.stageItems.length} stages`);

  const nonDas = work.stageItems.filter((item) => item.mode !== 'das');
  if (nonDas.length) {
    throw new Error(`endpoint harness currently supports DAS stage entries only; non-DAS stages: ${nonDas.map((s) => s.stageCode).join(', ')}`);
  }

  const isoMd5 = await md5File(vanillaIso);
  if (!flags['skip-md5'] && isoMd5.toLowerCase() !== VANILLA_MD5) {
    throw new Error(`vanilla ISO MD5 mismatch: expected ${VANILLA_MD5}, got ${isoMd5}`);
  }

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
      try { backend.proc.kill(); } catch (e) { /* ignore */ }
    }
  };

  try {
    await waitForReady(baseUrl);
    const setup = await api(baseUrl, 'GET', '/api/mex/setup/status');
    if (!setup.json.complete) throw new Error(`backend setup not complete: ${JSON.stringify(setup.json)}`);

    const projectName = flags.name || (manifest.build && manifest.build.projectName) || `duel-${manifest.agent || 'codex'}`;
    const projectDir = safeProjectDir(projectName);
    if (fs.existsSync(projectDir)) {
      if (!flags.force) throw new Error(`project already exists: ${projectDir} (pass --force to replace)`);
      log(`removing existing managed project ${projectDir}`);
      fs.rmSync(projectDir, { recursive: true, force: true });
    }

    log(`creating project "${projectName}" through /project/create`);
    const created = await api(baseUrl, 'POST', '/api/mex/project/create', { isoPath: vanillaIso, projectName });
    if (!created.json.success) throw new Error(`project/create failed: ${JSON.stringify(created.json)}`);
    const projectPath = created.json.projectPath;
    const opened = await api(baseUrl, 'POST', '/api/mex/project/open', { projectPath });
    if (!opened.json.success) throw new Error(`project/open failed: ${JSON.stringify(opened.json)}`);

    log(`batch importing ${work.importItems.length} costume DATs through /import-batch`);
    const imported = await api(baseUrl, 'POST', '/api/mex/import-batch', { items: work.importItems });
    if (!imported.json.success) throw new Error(`import-batch failed: ${JSON.stringify(imported.json)}`);

    log(`batch removing ${work.removeItems.length} original slots through /remove-batch`);
    const removed = await api(baseUrl, 'POST', '/api/mex/remove-batch', { items: work.removeItems });
    if (!removed.json.success) throw new Error(`remove-batch failed: ${JSON.stringify(removed.json)}`);

    log('installing DAS framework through /das/install');
    const dasInstall = await api(baseUrl, 'POST', '/api/mex/das/install', {});
    if (!dasInstall.json.success) throw new Error(`das/install failed: ${JSON.stringify(dasInstall.json)}`);
    for (const stage of work.stageItems) {
      log(`installing ${stage.stageCode} ${stage.displayName} behind hold ${stage.button || 'X'}`);
      const imp = await api(baseUrl, 'POST', '/api/mex/das/import', {
        stageCode: stage.stageCode,
        variantPath: stage.variantPath,
      });
      if (!imp.json.success) throw new Error(`das/import ${stage.stageCode} failed: ${JSON.stringify(imp.json)}`);
      const importedName = path.basename(imp.json.path || '', '.dat');
      const newName = `${importedName}(${stage.button || 'X'})`;
      const ren = await api(baseUrl, 'POST', '/api/mex/das/rename', {
        stageCode: stage.stageCode,
        oldName: importedName,
        newName,
      });
      if (!ren.json.success) throw new Error(`das/rename ${stage.stageCode} failed: ${JSON.stringify(ren.json)}`);
    }

    const duelDir = path.dirname(manifestPath);
    const exportsDir = path.join(duelDir, 'exports');
    const projectRecordDir = path.join(duelDir, 'project');
    fs.mkdirSync(exportsDir, { recursive: true });
    fs.mkdirSync(projectRecordDir, { recursive: true });
    fs.writeFileSync(path.join(projectRecordDir, 'project_name.txt'), `${projectName}\n`);

    const outputIsoName = `${projectName}.iso`;
    const backendIso = path.join(OUTPUT_DIR, outputIsoName);
    if (fs.existsSync(backendIso)) fs.rmSync(backendIso, { force: true });
    log(`exporting through /export/start -> output/${outputIsoName}`);
    const exp = await api(baseUrl, 'POST', '/api/mex/export/start', {
      filename: outputIsoName,
      cspCompression: flags.compression ? parseFloat(flags.compression) : 1.0,
      useColorSmash: !!flags['color-smash'],
    });
    if (!exp.json.success) throw new Error(`export/start failed: ${JSON.stringify(exp.json)}`);
    await waitForStableFile(backendIso, 800 * 1024 * 1024, 10 * 60 * 1000, 'ISO');
    const finalIso = path.join(exportsDir, 'final.iso');
    fs.copyFileSync(backendIso, finalIso);
    log(`copied final ISO to ${finalIso}`);

    let finalBundle = null;
    if (!flags['no-bundle']) {
      log('creating .ssbm through /bundle/export');
      const bundleStart = await api(baseUrl, 'POST', '/api/mex/bundle/export', {
        name: manifest.theme || projectName,
        description: `SSBM Nucleus duel submission by ${manifest.agent || 'unknown'}`,
        buildName: projectName,
        vanillaIsoPath: vanillaIso,
        exportedIsoPath: backendIso,
      });
      if (!bundleStart.json.success) throw new Error(`bundle/export failed: ${JSON.stringify(bundleStart.json)}`);
      const bundleId = bundleStart.json.export_id;
      const bundle = await waitForBundle(baseUrl, bundleId, 15 * 60 * 1000);
      if (!bundle) throw new Error(`bundle ${bundleId} did not finish; check backend log`);
      const storedBundle = path.join(STORAGE_DIR, 'bundles', `${bundleId}.ssbm`);
      finalBundle = path.join(exportsDir, 'final.ssbm');
      fs.copyFileSync(storedBundle, finalBundle);
      log(`copied final bundle to ${finalBundle}`);
    }

    if (!flags['no-update-manifest']) {
      updateManifest(manifestPath, { sourceIsoMd5: isoMd5, projectPath, finalIso, finalBundle });
      log(`updated manifest build paths in ${manifestPath}`);
    }

    const summary = { projectPath, finalIso, finalBundle, imports: work.importItems.length, stages: work.stageItems.length };
    console.log(`\nDUEL_MANIFEST ${JSON.stringify(summary)}`);
  } finally {
    await cleanup();
  }
}

main().catch((err) => {
  console.error(`[duel] ERROR: ${err.message}`);
  process.exit(1);
});
