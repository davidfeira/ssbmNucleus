const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  autoDetectFirstRunPaths,
  extractIsoLocationsFromDolphinIniText,
} = require('../../electron/first-run-autodetect');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'nucleus-first-run-'));
}

function writeFile(targetPath, contents) {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.writeFileSync(targetPath, contents);
}

function md5(contents) {
  return crypto.createHash('md5').update(contents).digest('hex');
}

test('extractIsoLocationsFromDolphinIniText resolves ISO paths and last filename', () => {
  const configPath = path.join('C:\\', 'Users', 'david', 'AppData', 'Roaming', 'Slippi Launcher', 'netplay', 'User', 'Config', 'Dolphin.ini');
  const iniText = [
    '[General]',
    'ISOPath0="D:\\Games\\Melee"',
    'ISOPath1=..\\..\\ISOs',
    'LastFilename="D:\\Games\\Melee\\vanilla.iso"',
  ].join('\n');

  const locations = extractIsoLocationsFromDolphinIniText(iniText, { configPath });

  assert.deepEqual(locations, [
    path.normalize('D:\\Games\\Melee\\vanilla.iso'),
    path.normalize('D:\\Games\\Melee'),
    path.resolve(path.dirname(configPath), '..\\..\\ISOs'),
  ]);
});

test('autoDetectFirstRunPaths prefers common vanilla-style names from Dolphin.ini locations', async () => {
  const appDataPath = makeTempDir();
  const slippiRoot = path.join(appDataPath, 'Slippi Launcher', 'netplay');
  const configPath = path.join(slippiRoot, 'User', 'Config', 'Dolphin.ini');
  const isoDir = path.join(appDataPath, 'Game ISOs');
  const vanillaContents = Buffer.from('vanilla melee');
  const wrongContents = Buffer.from('modded melee');
  const vanillaIsoPath = path.join(isoDir, 'vanilla melee 1.02.iso');

  writeFile(configPath, `[General]\nISOPath0=${isoDir}\n`);
  writeFile(path.join(isoDir, 'random-build.iso'), wrongContents);
  writeFile(vanillaIsoPath, vanillaContents);

  const result = await autoDetectFirstRunPaths({
    appDataPath,
    expectedMd5: md5(vanillaContents),
    maxHashes: 1,
  });

  assert.equal(result.success, true);
  assert.equal(result.isoPath, path.resolve(vanillaIsoPath));
  assert.equal(result.slippiPath, path.resolve(slippiRoot));
  assert.equal(result.configPath, path.resolve(configPath));
});

test('autoDetectFirstRunPaths still searches nearby Slippi folders when Dolphin.ini is missing', async () => {
  const appDataPath = makeTempDir();
  const netplayRoot = path.join(appDataPath, 'Slippi Launcher', 'netplay');
  const playbackRoot = path.join(appDataPath, 'Slippi Launcher', 'playback');
  const vanillaContents = Buffer.from('fallback vanilla iso');
  const isoPath = path.join(playbackRoot, 'GALE01 vanilla.gcm');

  fs.mkdirSync(netplayRoot, { recursive: true });
  fs.mkdirSync(playbackRoot, { recursive: true });
  writeFile(isoPath, vanillaContents);

  const result = await autoDetectFirstRunPaths({
    appDataPath,
    expectedMd5: md5(vanillaContents),
    maxHashes: 2,
  });

  assert.equal(result.success, true);
  assert.equal(result.isoPath, path.resolve(isoPath));
  assert.equal(result.slippiPath, path.resolve(netplayRoot));
  assert.equal(result.configPath, null);
});
