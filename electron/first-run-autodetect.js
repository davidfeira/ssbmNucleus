const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DEFAULT_VANILLA_ISO_MD5 = '0e63d4223b01d9aba596259dc155a174';
const GAMECUBE_DISC_SIZE = 1459978240;
const ISO_EXTENSIONS = new Set(['.iso', '.gcm']);

function parseIni(text) {
  const sections = {};
  let currentSection = '';
  sections[currentSection] = {};

  for (const rawLine of String(text || '').split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith(';') || line.startsWith('#')) {
      continue;
    }

    const sectionMatch = line.match(/^\[(.+?)\]$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      if (!sections[currentSection]) {
        sections[currentSection] = {};
      }
      continue;
    }

    const keyMatch = line.match(/^([^=]+?)\s*=\s*(.*)$/);
    if (keyMatch) {
      sections[currentSection][keyMatch[1].trim()] = keyMatch[2].trim();
    }
  }

  return sections;
}

function stripWrappingQuotes(value) {
  const text = String(value || '').trim();
  if (text.length >= 2 && text.startsWith('"') && text.endsWith('"')) {
    return text.slice(1, -1);
  }
  return text;
}

function uniqueStrings(values) {
  const seen = new Set();
  const result = [];

  for (const value of values) {
    const normalized = String(value || '').trim();
    if (!normalized) {
      continue;
    }
    const dedupeKey = normalized.toLowerCase();
    if (seen.has(dedupeKey)) {
      continue;
    }
    seen.add(dedupeKey);
    result.push(normalized);
  }

  return result;
}

function getDefaultSlippiRootCandidates(appDataPath) {
  if (!appDataPath) {
    return [];
  }

  return [
    path.join(appDataPath, 'Slippi Launcher', 'netplay'),
    path.join(appDataPath, 'Slippi Launcher', 'playback'),
  ];
}

function detectExistingSlippiRoots(options = {}) {
  const fsImpl = options.fsImpl || fs;
  const appDataPath = options.appDataPath || process.env.APPDATA || '';

  return getDefaultSlippiRootCandidates(appDataPath).filter((candidate) => {
    try {
      return fsImpl.existsSync(candidate) && fsImpl.statSync(candidate).isDirectory();
    } catch (error) {
      return false;
    }
  });
}

function getDolphinConfigPath(slippiRoot) {
  return path.join(slippiRoot, 'User', 'Config', 'Dolphin.ini');
}

function normalizeConfiguredLocation(value, configPath) {
  const cleaned = stripWrappingQuotes(value);
  if (!cleaned) {
    return '';
  }

  if (path.isAbsolute(cleaned)) {
    return path.normalize(cleaned);
  }

  if (configPath) {
    return path.resolve(path.dirname(configPath), cleaned);
  }

  return path.resolve(cleaned);
}

function extractIsoLocationsFromDolphinIniText(iniText, options = {}) {
  const configPath = options.configPath || '';
  const sections = parseIni(iniText);
  const general = sections.General || {};
  const locations = [];

  if (general.LastFilename) {
    locations.push(normalizeConfiguredLocation(general.LastFilename, configPath));
  }

  const isoKeys = Object.keys(general)
    .filter((key) => /^ISOPath\d+$/i.test(key))
    .sort((left, right) => {
      const leftIndex = Number(left.replace(/\D+/g, ''));
      const rightIndex = Number(right.replace(/\D+/g, ''));
      return leftIndex - rightIndex;
    });

  for (const key of isoKeys) {
    locations.push(normalizeConfiguredLocation(general[key], configPath));
  }

  return uniqueStrings(locations);
}

function isGameImageFile(filePath) {
  return ISO_EXTENSIONS.has(path.extname(filePath).toLowerCase());
}

function buildScopedSearchRoots(slippiRoot, configuredLocations, options = {}) {
  const fsImpl = options.fsImpl || fs;
  const roots = [...configuredLocations];

  if (slippiRoot) {
    roots.push(slippiRoot);

    const launcherRoot = path.dirname(slippiRoot);
    roots.push(launcherRoot);

    for (const sibling of ['netplay', 'playback']) {
      roots.push(path.join(launcherRoot, sibling));
    }
  }

  return uniqueStrings(roots).filter((candidate) => {
    try {
      return fsImpl.existsSync(candidate);
    } catch (error) {
      return false;
    }
  });
}

function collectIsoCandidatesFromRoot(rootPath, options = {}) {
  const fsImpl = options.fsImpl || fs;
  const maxDepth = options.maxDepth ?? 2;
  const maxFilesPerDirectory = options.maxFilesPerDirectory ?? 200;
  const results = [];
  const queue = [{ targetPath: rootPath, depth: 0 }];
  const visited = new Set();

  while (queue.length > 0) {
    const { targetPath, depth } = queue.shift();
    const normalizedTarget = path.resolve(targetPath);
    if (visited.has(normalizedTarget)) {
      continue;
    }
    visited.add(normalizedTarget);

    let stat;
    try {
      stat = fsImpl.statSync(normalizedTarget);
    } catch (error) {
      continue;
    }

    if (stat.isFile()) {
      if (isGameImageFile(normalizedTarget)) {
        results.push({
          path: normalizedTarget,
          size: stat.size,
        });
      }
      continue;
    }

    if (!stat.isDirectory() || depth > maxDepth) {
      continue;
    }

    let entries;
    try {
      entries = fsImpl.readdirSync(normalizedTarget, { withFileTypes: true });
    } catch (error) {
      continue;
    }

    const limitedEntries = entries.slice(0, maxFilesPerDirectory);
    for (const entry of limitedEntries) {
      const fullPath = path.join(normalizedTarget, entry.name);
      if (entry.isFile()) {
        if (isGameImageFile(fullPath)) {
          try {
            const fileStat = fsImpl.statSync(fullPath);
            results.push({
              path: fullPath,
              size: fileStat.size,
            });
          } catch (error) {
            // Ignore files that disappear mid-scan.
          }
        }
      } else if (entry.isDirectory() && depth < maxDepth) {
        queue.push({ targetPath: fullPath, depth: depth + 1 });
      }
    }
  }

  return results;
}

function candidatePriority(candidate) {
  const fileName = path.basename(candidate.path).toLowerCase();
  let score = 100;

  if (fileName.includes('gale01')) {
    score -= 50;
  }
  if (fileName.includes('vanilla')) {
    score -= 40;
  }
  if (fileName.includes('melee') || fileName.includes('smash') || fileName.includes('ssbm')) {
    score -= 30;
  }
  if (fileName.includes('1.02') || fileName.includes('102') || fileName.includes('ntsc')) {
    score -= 15;
  }
  if (candidate.size === GAMECUBE_DISC_SIZE) {
    score -= 10;
  }
  if (candidate.source === 'configured_path') {
    score -= 5;
  }

  return score;
}

function prioritizeIsoCandidates(candidates) {
  const deduped = new Map();

  for (const candidate of candidates) {
    const resolvedPath = path.resolve(candidate.path);
    const existing = deduped.get(resolvedPath);
    if (!existing || candidatePriority(candidate) < candidatePriority(existing)) {
      deduped.set(resolvedPath, {
        ...candidate,
        path: resolvedPath,
      });
    }
  }

  return Array.from(deduped.values()).sort((left, right) => {
    const scoreDiff = candidatePriority(left) - candidatePriority(right);
    if (scoreDiff !== 0) {
      return scoreDiff;
    }
    return left.path.localeCompare(right.path);
  });
}

async function hashFileMd5(filePath, options = {}) {
  const fsImpl = options.fsImpl || fs;
  const cryptoImpl = options.cryptoImpl || crypto;

  return new Promise((resolve, reject) => {
    const hash = cryptoImpl.createHash('md5');
    const stream = fsImpl.createReadStream(filePath, { highWaterMark: 8 * 1024 * 1024 });

    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('error', reject);
    stream.on('end', () => resolve(hash.digest('hex')));
  });
}

function buildNotFoundReason(context) {
  if (!context.detectedSlippiPaths.length) {
    return 'no_slippi_install_found';
  }
  if (!context.candidateFiles.length) {
    if (!context.configPaths.length) {
      return 'no_dolphin_ini_found';
    }
    if (!context.configuredLocations.length) {
      return 'no_iso_locations_in_dolphin_ini';
    }
    return 'no_iso_candidates_found';
  }
  return 'no_matching_vanilla_iso_found';
}

async function autoDetectFirstRunPaths(options = {}) {
  const fsImpl = options.fsImpl || fs;
  const appDataPath = options.appDataPath || process.env.APPDATA || '';
  const expectedMd5 = String(options.expectedMd5 || DEFAULT_VANILLA_ISO_MD5).toLowerCase();
  const maxDepth = options.maxDepth ?? 2;
  const maxHashes = options.maxHashes ?? 12;

  const detectedSlippiPaths = detectExistingSlippiRoots({ fsImpl, appDataPath });
  const preferredSlippiPath = detectedSlippiPaths[0] || null;
  const configPaths = [];
  const configuredLocations = [];
  const candidateFiles = [];
  const checkedFiles = [];

  for (const slippiPath of detectedSlippiPaths) {
    const configPath = getDolphinConfigPath(slippiPath);
    const availableConfigPath = fsImpl.existsSync(configPath) ? configPath : null;
    let locations = [];

    if (availableConfigPath) {
      configPaths.push(availableConfigPath);

      let iniText = '';
      try {
        iniText = fsImpl.readFileSync(availableConfigPath, 'utf8');
        locations = extractIsoLocationsFromDolphinIniText(iniText, { configPath: availableConfigPath });
      } catch (error) {
        locations = [];
      }
    }
    configuredLocations.push(...locations);

    const searchRoots = buildScopedSearchRoots(slippiPath, locations, { fsImpl });
    for (const searchRoot of searchRoots) {
      const source = locations.includes(searchRoot) ? 'configured_path' : 'slippi_local';
      for (const candidate of collectIsoCandidatesFromRoot(searchRoot, { fsImpl, maxDepth })) {
        candidateFiles.push({
          ...candidate,
          source,
          slippiPath,
          configPath: availableConfigPath,
          searchRoot,
        });
      }
    }
  }

  const prioritizedCandidates = prioritizeIsoCandidates(candidateFiles);

  for (const candidate of prioritizedCandidates.slice(0, maxHashes)) {
    const md5 = await hashFileMd5(candidate.path, { fsImpl });
    const matches = md5.toLowerCase() === expectedMd5;

    checkedFiles.push({
      path: candidate.path,
      md5,
      matches,
    });

    if (matches) {
      return {
        success: true,
        isoPath: candidate.path,
        slippiPath: preferredSlippiPath,
        isoSourceSlippiPath: candidate.slippiPath,
        configPath: candidate.configPath,
        searchedRoots: uniqueStrings(prioritizedCandidates.map((item) => item.searchRoot)),
        configuredLocations: uniqueStrings(configuredLocations),
        checkedFiles,
        candidateFiles: prioritizedCandidates.map((item) => item.path),
      };
    }
  }

  return {
    success: false,
    isoPath: null,
    slippiPath: preferredSlippiPath,
    configPath: configPaths[0] || null,
    reason: buildNotFoundReason({
      detectedSlippiPaths,
      configPaths,
      configuredLocations,
      candidateFiles: prioritizedCandidates,
    }),
    detectedSlippiPaths,
    configuredLocations: uniqueStrings(configuredLocations),
    candidateFiles: prioritizedCandidates.map((item) => item.path),
    checkedFiles,
  };
}

module.exports = {
  DEFAULT_VANILLA_ISO_MD5,
  GAMECUBE_DISC_SIZE,
  autoDetectFirstRunPaths,
  buildScopedSearchRoots,
  candidatePriority,
  collectIsoCandidatesFromRoot,
  detectExistingSlippiRoots,
  extractIsoLocationsFromDolphinIniText,
  getDefaultSlippiRootCandidates,
  getDolphinConfigPath,
  hashFileMd5,
  isGameImageFile,
  parseIni,
  prioritizeIsoCandidates,
};
