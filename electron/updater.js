/**
 * In-app updater - vAMP-style manifest check against the R2 releases bucket.
 *
 * Manifest: https://releases.ssbmnucleus.net/windows/latest.json
 *   { version, notes, pub_date, platforms: { 'windows-x86_64': { url, sha256, size } } }
 * (written by scripts/build/release_to_r2.py)
 *
 * check():   fetch manifest, compare to app.getVersion() -> update info or null
 * install(): download the installer to temp, verify sha256, launch it, quit.
 */
const { app } = require('electron');
const crypto = require('crypto');
const fs = require('fs');
const https = require('https');
const path = require('path');
const { spawn } = require('child_process');

const MANIFEST_URL = 'https://releases.ssbmnucleus.net/windows/latest.json';
const PLATFORM_KEY = 'windows-x86_64';

let cachedUpdate = null; // last update info returned by check(), used by install()
let installing = false;

function compareVersions(a, b) {
  const pa = String(a).split('.').map((n) => parseInt(n, 10) || 0);
  const pb = String(b).split('.').map((n) => parseInt(n, 10) || 0);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const da = pa[i] || 0;
    const db = pb[i] || 0;
    if (da !== db) return da > db ? 1 : -1;
  }
  return 0;
}

function fetchJson(url, redirectsLeft = 3) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'Cache-Control': 'no-cache' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && redirectsLeft > 0) {
        res.resume();
        resolve(fetchJson(res.headers.location, redirectsLeft - 1));
        return;
      }
      if (res.statusCode !== 200) {
        res.resume();
        reject(new Error(`Update server returned HTTP ${res.statusCode}`));
        return;
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (err) {
          reject(new Error('Update manifest is not valid JSON'));
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(15000, () => req.destroy(new Error('Update check timed out')));
  });
}

function downloadFile(url, destPath, onProgress, redirectsLeft = 3) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && redirectsLeft > 0) {
        res.resume();
        resolve(downloadFile(res.headers.location, destPath, onProgress, redirectsLeft - 1));
        return;
      }
      if (res.statusCode !== 200) {
        res.resume();
        reject(new Error(`Download failed: HTTP ${res.statusCode}`));
        return;
      }

      const total = parseInt(res.headers['content-length'], 10) || 0;
      let received = 0;
      const hash = crypto.createHash('sha256');
      const out = fs.createWriteStream(destPath);

      res.on('data', (chunk) => {
        received += chunk.length;
        hash.update(chunk);
        if (onProgress && total > 0) {
          onProgress(received, total);
        }
      });

      res.pipe(out);

      out.on('finish', () => resolve({ sha256: hash.digest('hex'), size: received }));
      out.on('error', (err) => {
        res.resume();
        reject(err);
      });
      res.on('error', reject);
    });
    req.on('error', reject);
  });
}

/**
 * Check the manifest for a newer version.
 * @returns {Promise<{version, notes, url, sha256, size}|null>}
 */
async function check() {
  const manifest = await fetchJson(`${MANIFEST_URL}?t=${Date.now()}`);
  const platform = manifest.platforms && manifest.platforms[PLATFORM_KEY];
  if (!manifest.version || !platform || !platform.url) {
    throw new Error('Update manifest is missing required fields');
  }

  const current = app.getVersion();
  console.log(`[Updater] current=${current} latest=${manifest.version}`);
  if (compareVersions(manifest.version, current) <= 0) {
    cachedUpdate = null;
    return null;
  }

  cachedUpdate = {
    version: manifest.version,
    notes: manifest.notes || '',
    url: platform.url,
    sha256: platform.sha256 || null,
    size: platform.size || 0,
  };
  return cachedUpdate;
}

/**
 * Download the cached update, verify it, launch the installer, and quit.
 * @param {function(received:number, total:number)} onProgress
 */
async function install(onProgress) {
  if (!cachedUpdate) {
    throw new Error('No update available - run a check first');
  }
  if (installing) {
    throw new Error('Update already in progress');
  }
  installing = true;

  try {
    const fileName = path.basename(new URL(cachedUpdate.url).pathname);
    const destPath = path.join(app.getPath('temp'), fileName);

    console.log(`[Updater] Downloading ${cachedUpdate.url} -> ${destPath}`);
    const result = await downloadFile(cachedUpdate.url, destPath, onProgress);

    if (cachedUpdate.sha256 && result.sha256 !== cachedUpdate.sha256) {
      fs.unlinkSync(destPath);
      throw new Error('Downloaded installer failed checksum verification');
    }
    if (cachedUpdate.size && result.size !== cachedUpdate.size) {
      fs.unlinkSync(destPath);
      throw new Error(`Downloaded installer is incomplete (${result.size} of ${cachedUpdate.size} bytes)`);
    }

    console.log('[Updater] Verified - launching installer and quitting');
    const child = spawn(destPath, [], { detached: true, stdio: 'ignore' });
    child.unref();

    // Give the installer a moment to start before tearing down the app
    // (before-quit shuts down the Flask backend so its files aren't locked).
    setTimeout(() => app.quit(), 1500);
  } finally {
    installing = false;
  }
}

module.exports = { check, install };
