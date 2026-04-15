#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const cp = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const ARTIFACTS_ROOT = path.join(ROOT_DIR, 'tests', 'artifacts', 'dolphin');
const INPUT_HELPER = path.join(__dirname, 'win-input.ps1');
const WINDOW_HELPER = path.join(__dirname, 'win-window.ps1');
const DEFAULT_SCENARIO = path.join(__dirname, 'scenarios', 'boot-and-hold-a.json');

function printHelp() {
  console.log(`Dolphin smoke driver

Usage:
  node tests/dolphin/driver.js --iso "C:\\path\\to\\game.iso" [options]

Options:
  --iso <path>                ISO to boot. Required unless --help is used.
  --dolphin <path>            Dolphin executable. Defaults to Slippi netplay if found.
  --scenario <path>           Scenario JSON. Default: tests/dolphin/scenarios/boot-and-hold-a.json
  --template-user-dir <path>  Template Dolphin User dir. Defaults to "<dolphin dir>\\User" when present.
  --run-dir <path>            Use an explicit artifact directory for this run.
  --keep-open                 Leave Dolphin running after the scenario finishes.
  --dry-run                   Build the isolated config and print the launch plan without starting Dolphin.
  --help                      Show this message.

Notes:
  - This harness is Windows-only.
  - Input is sent with a PowerShell helper that focuses the Dolphin window and emits keyboard events.
  - Screenshots are captured from the Dolphin window into each run directory.
  - The temporary run copy forces a known GCPad1 keyboard mapping:
      A=X, B=Z, X=C, Y=S, Z=D, Start=ENTER, stick=arrow keys, L=Q, R=W
`);
}

function parseArgs(argv) {
  const result = {
    keepOpen: false,
    dryRun: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--help' || token === '-h') {
      result.help = true;
      continue;
    }
    if (token === '--keep-open') {
      result.keepOpen = true;
      continue;
    }
    if (token === '--dry-run') {
      result.dryRun = true;
      continue;
    }
    if (!token.startsWith('--')) {
      throw new Error(`Unexpected argument: ${token}`);
    }
    const key = token.slice(2);
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for --${key}`);
    }
    result[key] = value;
    i += 1;
  }

  return result;
}

function assertWindows() {
  if (process.platform !== 'win32') {
    throw new Error('tests/dolphin/driver.js currently only supports Windows.');
  }
}

function timestampSlug() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function safeSlug(value) {
  return String(value || 'run')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64) || 'run';
}

function safeFileName(value) {
  return String(value || 'capture')
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 100) || 'capture';
}

function ensureExists(targetPath, label) {
  if (!fs.existsSync(targetPath)) {
    throw new Error(`${label} does not exist: ${targetPath}`);
  }
}

function firstExisting(paths) {
  for (const candidate of paths) {
    if (candidate && fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return null;
}

function detectDefaultDolphin() {
  const appData = process.env.APPDATA || '';
  return firstExisting([
    process.env.SLIPPI_DOLPHIN_EXE,
    path.join(appData, 'Slippi Launcher', 'netplay', 'Slippi Dolphin.exe'),
    path.join(appData, 'Slippi Launcher', 'playback', 'Slippi Dolphin.exe'),
  ]);
}

function detectTemplateUserDir(dolphinExe) {
  if (!dolphinExe) {
    return null;
  }
  const siblingUserDir = path.join(path.dirname(dolphinExe), 'User');
  if (fs.existsSync(siblingUserDir) && fs.statSync(siblingUserDir).isDirectory()) {
    return siblingUserDir;
  }
  return null;
}

function parseIni(text) {
  const sections = new Map();
  let currentSection = '';
  sections.set(currentSection, new Map());

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith(';') || line.startsWith('#')) {
      continue;
    }
    const sectionMatch = line.match(/^\[(.+?)\]$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      if (!sections.has(currentSection)) {
        sections.set(currentSection, new Map());
      }
      continue;
    }
    const keyMatch = line.match(/^([^=]+?)\s*=\s*(.*)$/);
    if (keyMatch) {
      sections.get(currentSection).set(keyMatch[1].trim(), keyMatch[2]);
    }
  }

  return sections;
}

function stringifyIni(sections) {
  const lines = [];
  let firstSection = true;

  for (const [sectionName, values] of sections.entries()) {
    if (sectionName !== '') {
      if (!firstSection) {
        lines.push('');
      }
      lines.push(`[${sectionName}]`);
      firstSection = false;
    }
    for (const [key, value] of values.entries()) {
      lines.push(`${key} = ${value}`);
    }
  }

  return `${lines.join(os.EOL)}${os.EOL}`;
}

function upsertIniValue(sections, sectionName, key, value) {
  if (!sections.has(sectionName)) {
    sections.set(sectionName, new Map());
  }
  sections.get(sectionName).set(key, value);
}

function writeIni(filePath, mutate) {
  const source = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : '';
  const sections = parseIni(source);
  mutate(sections);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, stringifyIni(sections), 'utf8');
}

function copyTemplateConfig(templateUserDir, targetUserDir) {
  const sourceConfigDir = templateUserDir ? path.join(templateUserDir, 'Config') : null;
  const targetConfigDir = path.join(targetUserDir, 'Config');
  fs.mkdirSync(targetConfigDir, { recursive: true });

  if (sourceConfigDir && fs.existsSync(sourceConfigDir)) {
    fs.cpSync(sourceConfigDir, targetConfigDir, { recursive: true });
  }
}

function patchDolphinConfig(userDir) {
  const dolphinIni = path.join(userDir, 'Config', 'Dolphin.ini');
  writeIni(dolphinIni, (sections) => {
    upsertIniValue(sections, 'Input', 'BackgroundInput', 'True');
    upsertIniValue(sections, 'Interface', 'ConfirmStop', 'False');
    upsertIniValue(sections, 'Interface', 'PauseOnFocusLost', 'False');
    upsertIniValue(sections, 'Display', 'Fullscreen', 'False');
    upsertIniValue(sections, 'Display', 'RenderWindowAutoSize', 'False');
    upsertIniValue(sections, 'Display', 'RenderWindowWidth', '1280');
    upsertIniValue(sections, 'Display', 'RenderWindowHeight', '960');
  });

  const gcPadIni = path.join(userDir, 'Config', 'GCPadNew.ini');
  writeIni(gcPadIni, (sections) => {
    const section = 'GCPad1';
    upsertIniValue(sections, section, 'Device', 'DInput/0/Keyboard Mouse');
    upsertIniValue(sections, section, 'Buttons/A', 'X');
    upsertIniValue(sections, section, 'Buttons/B', 'Z');
    upsertIniValue(sections, section, 'Buttons/X', 'C');
    upsertIniValue(sections, section, 'Buttons/Y', 'S');
    upsertIniValue(sections, section, 'Buttons/Z', 'D');
    upsertIniValue(sections, section, 'Buttons/Start', 'RETURN');
    upsertIniValue(sections, section, 'Main Stick/Up', 'UP');
    upsertIniValue(sections, section, 'Main Stick/Down', 'DOWN');
    upsertIniValue(sections, section, 'Main Stick/Left', 'LEFT');
    upsertIniValue(sections, section, 'Main Stick/Right', 'RIGHT');
    upsertIniValue(sections, section, 'Main Stick/Modifier', 'LSHIFT');
    upsertIniValue(sections, section, 'Main Stick/Modifier/Range', '50.000000000000000');
    upsertIniValue(sections, section, 'C-Stick/Up', 'I');
    upsertIniValue(sections, section, 'C-Stick/Down', 'K');
    upsertIniValue(sections, section, 'C-Stick/Left', 'J');
    upsertIniValue(sections, section, 'C-Stick/Right', 'L');
    upsertIniValue(sections, section, 'C-Stick/Modifier', 'LCONTROL');
    upsertIniValue(sections, section, 'C-Stick/Modifier/Range', '50.000000000000000');
    upsertIniValue(sections, section, 'Triggers/L', 'Q');
    upsertIniValue(sections, section, 'Triggers/R', 'W');
    upsertIniValue(sections, section, 'D-Pad/Up', 'T');
    upsertIniValue(sections, section, 'D-Pad/Down', 'G');
    upsertIniValue(sections, section, 'D-Pad/Left', 'F');
    upsertIniValue(sections, section, 'D-Pad/Right', 'H');
  });
}

function readScenario(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(raw);
  if (!Array.isArray(data.steps)) {
    throw new Error(`Scenario is missing a steps array: ${filePath}`);
  }
  return data;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createLogger(runDir) {
  fs.mkdirSync(runDir, { recursive: true });
  const logFile = path.join(runDir, 'driver.log');
  return (message) => {
    const line = `[${new Date().toISOString()}] ${message}`;
    console.log(line);
    fs.appendFileSync(logFile, `${line}${os.EOL}`, 'utf8');
  };
}

function runHelper(action, pid, key, durationMs) {
  const args = [
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    INPUT_HELPER,
    '-ProcessId',
    String(pid),
    '-Action',
    action,
  ];

  if (key) {
    args.push('-Key', key);
  }
  if (durationMs !== undefined && durationMs !== null) {
    args.push('-DurationMs', String(durationMs));
  }

  const result = cp.spawnSync('powershell.exe', args, {
    cwd: ROOT_DIR,
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    const stderr = (result.stderr || '').trim();
    const stdout = (result.stdout || '').trim();
    throw new Error(stderr || stdout || `PowerShell helper failed for action ${action}`);
  }
}

function runWindowHelper(action, pid, outputPath) {
  const args = [
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    WINDOW_HELPER,
    '-ProcessId',
    String(pid),
    '-Action',
    action,
  ];

  if (outputPath) {
    args.push('-OutputPath', outputPath);
  }

  const result = cp.spawnSync('powershell.exe', args, {
    cwd: ROOT_DIR,
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    const stderr = (result.stderr || '').trim();
    const stdout = (result.stdout || '').trim();
    throw new Error(stderr || stdout || `PowerShell window helper failed for action ${action}`);
  }

  return (result.stdout || '').trim();
}

function captureWindow(child, runDir, name, log) {
  if (child.exitCode !== null) {
    throw new Error('Cannot capture a screenshot because Dolphin has already exited.');
  }

  const screenshotDir = path.join(runDir, 'screenshots');
  fs.mkdirSync(screenshotDir, { recursive: true });

  const targetPath = path.join(screenshotDir, `${safeFileName(name)}.png`);
  runWindowHelper('capture', child.pid, targetPath);
  log(`Captured screenshot: ${targetPath}`);
  return targetPath;
}

function captureWindowSafe(child, runDir, name, log) {
  try {
    return captureWindow(child, runDir, name, log);
  } catch (error) {
    log(`Screenshot capture skipped: ${error.message}`);
    return null;
  }
}

async function runScenario(child, scenario, runDir, log) {
  for (let index = 0; index < scenario.steps.length; index += 1) {
    const step = scenario.steps[index];
    if (child.exitCode !== null) {
      throw new Error(`Dolphin exited before step ${index + 1} completed.`);
    }

    const type = step.type;
    log(`Step ${index + 1}/${scenario.steps.length}: ${JSON.stringify(step)}`);

    if (type === 'wait') {
      await sleep(step.ms || 0);
      continue;
    }
    if (type === 'focus') {
      runHelper('focus', child.pid);
      continue;
    }
    if (type === 'tap') {
      runHelper('tap', child.pid, step.key, step.durationMs ?? 80);
      continue;
    }
    if (type === 'keyDown') {
      runHelper('keyDown', child.pid, step.key);
      continue;
    }
    if (type === 'keyUp') {
      runHelper('keyUp', child.pid, step.key);
      continue;
    }
    if (type === 'screenshot' || type === 'checkpoint') {
      const label = step.name || `step-${index + 1}`;
      captureWindow(child, runDir, label, log);
      continue;
    }

    throw new Error(`Unsupported step type: ${type}`);
  }
}

function killProcessTree(pid, log) {
  const result = cp.spawnSync('taskkill.exe', ['/PID', String(pid), '/T', '/F'], {
    cwd: ROOT_DIR,
    encoding: 'utf8',
  });
  if (result.status === 0) {
    log(`Stopped Dolphin process tree for PID ${pid}.`);
    return;
  }

  const stderr = (result.stderr || '').trim();
  const stdout = (result.stdout || '').trim();
  throw new Error(stderr || stdout || `Failed to stop Dolphin PID ${pid}`);
}

function buildRunDir(explicitRunDir, scenarioName) {
  if (explicitRunDir) {
    const resolved = path.resolve(ROOT_DIR, explicitRunDir);
    if (fs.existsSync(resolved) && fs.readdirSync(resolved).length > 0) {
      throw new Error(`Run directory already exists and is not empty: ${resolved}`);
    }
    return resolved;
  }

  return path.join(ARTIFACTS_ROOT, `${timestampSlug()}-${safeSlug(scenarioName)}`);
}

async function main() {
  assertWindows();

  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  if (!args.iso) {
    throw new Error('--iso is required.');
  }

  const dolphinExe = path.resolve(args.dolphin || detectDefaultDolphin() || '');
  if (!dolphinExe || !fs.existsSync(dolphinExe)) {
    throw new Error('Could not find a Dolphin executable. Pass --dolphin explicitly.');
  }

  const isoPath = path.resolve(args.iso);
  ensureExists(isoPath, 'ISO');
  ensureExists(INPUT_HELPER, 'PowerShell input helper');
  ensureExists(WINDOW_HELPER, 'PowerShell window helper');

  const scenarioPath = path.resolve(args.scenario || DEFAULT_SCENARIO);
  ensureExists(scenarioPath, 'Scenario');
  const scenario = readScenario(scenarioPath);

  const templateUserDir = args['template-user-dir']
    ? path.resolve(args['template-user-dir'])
    : detectTemplateUserDir(dolphinExe);

  if (templateUserDir) {
    ensureExists(templateUserDir, 'Template user dir');
  }

  const runDir = buildRunDir(args['run-dir'], scenario.name || path.basename(scenarioPath, '.json'));
  const log = createLogger(runDir);
  const userDir = path.join(runDir, 'User');

  fs.mkdirSync(runDir, { recursive: true });
  fs.mkdirSync(userDir, { recursive: true });
  fs.mkdirSync(path.join(runDir, 'screenshots'), { recursive: true });
  copyTemplateConfig(templateUserDir, userDir);
  patchDolphinConfig(userDir);

  const metadata = {
    createdAt: new Date().toISOString(),
    dolphinExe,
    isoPath,
    scenarioPath,
    templateUserDir,
    runDir,
    userDir,
    dryRun: args.dryRun,
  };

  fs.writeFileSync(path.join(runDir, 'run.json'), JSON.stringify(metadata, null, 2), 'utf8');

  log(`Run directory: ${runDir}`);
  log(`Dolphin executable: ${dolphinExe}`);
  log(`ISO: ${isoPath}`);
  log(`Scenario: ${scenarioPath}`);
  log(`Template user dir: ${templateUserDir || '<none>'}`);

  if (args.dryRun) {
    log('Dry run complete. Dolphin was not started.');
    return;
  }

  const dolphinArgs = ['-u', userDir, '-b', '-e', isoPath];
  log(`Launching Dolphin with args: ${JSON.stringify(dolphinArgs)}`);

  let child;
  try {
    child = cp.spawn(dolphinExe, dolphinArgs, {
      cwd: path.dirname(dolphinExe),
      windowsHide: false,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (error) {
    throw new Error(`Failed to launch Dolphin: ${error.message}`);
  }

  fs.writeFileSync(path.join(runDir, 'dolphin.pid'), `${child.pid}${os.EOL}`, 'utf8');
  child.stdout.on('data', (chunk) => {
    fs.appendFileSync(path.join(runDir, 'dolphin.stdout.log'), chunk);
  });
  child.stderr.on('data', (chunk) => {
    fs.appendFileSync(path.join(runDir, 'dolphin.stderr.log'), chunk);
  });

  let childExit = null;
  child.on('exit', (code, signal) => {
    childExit = { code, signal, exitedAt: new Date().toISOString() };
    fs.writeFileSync(path.join(runDir, 'dolphin.exit.json'), JSON.stringify(childExit, null, 2), 'utf8');
    log(`Dolphin exited with code=${code} signal=${signal}`);
  });

  try {
    await runScenario(child, scenario, runDir, log);
    captureWindowSafe(child, runDir, 'final', log);
    log('Scenario completed.');
  } catch (error) {
    log(`Scenario failed: ${error.message}`);
    captureWindowSafe(child, runDir, 'failure', log);
    if (child.exitCode === null) {
      killProcessTree(child.pid, log);
    }
    throw error;
  }

  if (!args.keepOpen && child.exitCode === null) {
    killProcessTree(child.pid, log);
  } else if (args.keepOpen) {
    log('Leaving Dolphin running because --keep-open was set.');
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
