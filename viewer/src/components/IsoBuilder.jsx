import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { playSound } from '../utils/sounds';
import { API_URL, BACKEND_URL } from '../config';
import { getProgressMessage } from './shared/progressText';
import ProgressPanel from './export/ProgressPanel';
import ExportModePicker from './export/ExportModePicker';
import AutoTexturePanel from './export/AutoTexturePanel';
import ManualListenPanel from './export/ManualListenPanel';
import BundleForm from './export/BundleForm';
import TestInGamePanel from './export/TestInGamePanel';
import './IsoBuilder.css';

// CSS screen order for the manual scan — matches the character select layout.
// Sheik is last since she shares Zelda's CSP slot.
const CSS_SCAN_ORDER = [
  'Dr. Mario', 'Mario', 'Luigi', 'Bowser', 'Peach', 'Yoshi',
  'Donkey Kong', 'Captain Falcon', 'Ganondorf', 'Young Link', 'Link', 'Zelda',
  'Samus', 'Kirby', 'Ice Climbers', 'Ness', 'Fox', 'Falco',
  'Pichu', 'Pikachu', 'Jigglypuff', 'Mewtwo', 'Mr. Game & Watch', 'Marth', 'Roy',
  'Sheik',
];

// phase: choose | exporting | autoTexture | listening | done | error
const IsoBuilder = ({ onClose, projectName = 'game' }) => {
  const getDefaultFilename = () => {
    const now = new Date();
    const date = now.toISOString().slice(0, 10);
    const time = now.toTimeString().slice(0, 5).replace(':', '-');
    return `${projectName}_${date}_${time}.iso`;
  };

  // --- top-level flow ---
  const [phase, setPhase] = useState('choose');
  const [filename, setFilename] = useState(getDefaultFilename());
  const [error, setError] = useState(null);

  // --- export options ---
  const [cspCompression, setCspCompression] = useState(1.0);
  const [useColorSmash, setUseColorSmash] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [recommendedCompression, setRecommendedCompression] = useState(1.0);
  const [costumeCount, setCostumeCount] = useState(0);

  // --- ISO export progress ---
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [exportedIsoPath, setExportedIsoPath] = useState(null);
  const [buildId, setBuildId] = useState(null);
  const [usedTexturePack, setUsedTexturePack] = useState(false);
  const [texturePackPath, setTexturePackPath] = useState(null);

  // settings paths (read once)
  const [slippiDolphinPath] = useState(() => localStorage.getItem('slippi_dolphin_path') || '');

  // --- auto texture pack ---
  const [autoProgress, setAutoProgress] = useState({ percentage: 0, message: '', stage: '' });
  const [autoResult, setAutoResult] = useState(null);
  const [autoError, setAutoError] = useState(null);

  // --- manual scan (fallback) ---
  const [textureProgress, setTextureProgress] = useState({ matched: 0, total: 0, percentage: 0 });
  const [characters, setCharacters] = useState([]);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const textureModeRef = useRef('auto'); // 'auto' | 'manual'

  // --- patch ---
  const [showPatchForm, setShowPatchForm] = useState(false);
  const [patchName, setPatchName] = useState('');
  const [patchDescription, setPatchDescription] = useState('');
  const [creatingPatch, setCreatingPatch] = useState(false);
  const [patchProgress, setPatchProgress] = useState(0);
  const [patchMessage, setPatchMessage] = useState('');
  const [patchComplete, setPatchComplete] = useState(false);
  const [patchError, setPatchError] = useState(null);
  const [patchResult, setPatchResult] = useState(null);
  const patchCreateIdRef = useRef(null);

  // --- bundle ---
  const [showBundleForm, setShowBundleForm] = useState(false);
  const [bundleName, setBundleName] = useState('');
  const [bundleDescription, setBundleDescription] = useState('');
  const [bundleImage, setBundleImage] = useState(null);
  const [bundleImagePreview, setBundleImagePreview] = useState(null);
  const [bundleExporting, setBundleExporting] = useState(false);
  const [bundleProgress, setBundleProgress] = useState(0);
  const [bundleMessage, setBundleMessage] = useState('');
  const [bundleComplete, setBundleComplete] = useState(false);
  const [bundleError, setBundleError] = useState(null);
  const [bundleResult, setBundleResult] = useState(null);
  const bundleExportIdRef = useRef(null);

  // --- test in game ---
  const [testing, setTesting] = useState(false);
  const [testStage, setTestStage] = useState('');
  const [testProgress, setTestProgress] = useState(0);
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState(null);
  const [testManifestPath, setTestManifestPath] = useState('');
  const [showTestAdvanced, setShowTestAdvanced] = useState(false);

  const socketRef = useRef(null);

  // Functions the socket handlers need to call — kept on a ref so the socket
  // effect can run once (deps []) without going stale.
  const liveRef = useRef({});

  // ---- texture pack: auto naming (no Dolphin) ----
  const startAutoTexture = async (bId) => {
    setAutoProgress({ percentage: 0, message: 'Starting…', stage: '' });
    setAutoResult(null);
    setAutoError(null);
    setPhase('autoTexture');
    try {
      const res = await fetch(`${API_URL}/texture-pack/auto-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ buildId: bId, slippiPath: slippiDolphinPath }),
      });
      const data = await res.json();
      if (!data.success) {
        setAutoError(data.error || 'Failed to start auto texture pack');
        playSound('error');
      }
    } catch (err) {
      setAutoError(`Failed to start auto texture pack: ${err.message}`);
      playSound('error');
    }
  };

  // ---- texture pack: manual live scan (fallback) ----
  const startManualListening = async (bId) => {
    setPhase('listening');
    try {
      const response = await fetch(`${API_URL}/texture-pack/start-listening`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ buildId: bId, slippiPath: slippiDolphinPath }),
      });
      const result = await response.json();
      if (result.success) {
        const chars = result.characters || [];
        const sortedChars = [...chars].sort((a, b) => {
          const aIdx = CSS_SCAN_ORDER.indexOf(a.name);
          const bIdx = CSS_SCAN_ORDER.indexOf(b.name);
          if (aIdx === -1 && bIdx === -1) return a.name.localeCompare(b.name);
          if (aIdx === -1) return 1;
          if (bIdx === -1) return -1;
          return aIdx - bIdx;
        });
        const filteredTotal = sortedChars.reduce((sum, c) => sum + c.total, 0);
        setTextureProgress({ matched: 0, total: filteredTotal, percentage: 0 });
        setCharacters(sortedChars);
        setCurrentCharIndex(0);
      }
    } catch (err) {
      console.error('Failed to start texture listening:', err);
    }
  };

  liveRef.current.startAutoTexture = startAutoTexture;
  liveRef.current.startManualListening = startManualListening;

  // ---- WebSocket wiring (connect once) ----
  useEffect(() => {
    const socket = io(BACKEND_URL);
    socketRef.current = socket;

    socket.on('connect', () => console.log('Connected to WebSocket'));

    // ISO export
    socket.on('export_progress', (data) => {
      setProgress(data.percentage);
      setMessage(data.message || 'Exporting assets...');
    });

    socket.on('export_complete', (data) => {
      setProgress(100);
      setMessage('Export complete!');
      setExportedIsoPath(data.path);
      playSound('achievement');

      if (data.texturePackMode && data.buildId) {
        setBuildId(data.buildId);
        setUsedTexturePack(true);
        setTextureProgress({ matched: 0, total: data.totalCostumes || 0, percentage: 0 });
        if (textureModeRef.current === 'manual') {
          liveRef.current.startManualListening(data.buildId);
        } else {
          liveRef.current.startAutoTexture(data.buildId);
        }
      } else {
        setPhase('done');
      }
    });

    socket.on('export_error', (data) => {
      playSound('error');
      setError(data.error);
      setPhase('error');
    });

    // auto texture pack
    socket.on('texture_auto_progress', (data) => setAutoProgress(data));
    socket.on('texture_auto_complete', (data) => {
      setAutoResult(data);
      if (data.texturePackPath) setTexturePackPath(data.texturePackPath);
      playSound('achievement');
    });
    socket.on('texture_auto_error', (data) => {
      setAutoError(data.error);
      playSound('error');
    });

    // manual scan
    socket.on('texture_matched', (data) => {
      setCharacters((prev) => {
        const updated = prev.map((char) =>
          char.name === data.character
            ? {
                ...char,
                matched: char.matched + 1,
                costumes: char.costumes.map((c) =>
                  c.index === data.costumeIndex ? { ...c, matched: true } : c
                ),
              }
            : char
        );
        const matchedCharIdx = updated.findIndex((c) => c.name === data.character);
        const matchedChar = updated[matchedCharIdx];
        if (matchedChar && matchedChar.matched + 1 >= matchedChar.total) {
          const nextIncomplete = updated.findIndex((c) => c.matched < c.total);
          if (nextIncomplete !== -1) setCurrentCharIndex(nextIncomplete);
        } else if (matchedCharIdx !== -1) {
          setCurrentCharIndex(matchedCharIdx);
        }
        return updated;
      });
    });
    socket.on('texture_progress', (data) => setTextureProgress(data));

    // patch
    socket.on('xdelta_create_progress', (data) => {
      if (patchCreateIdRef.current && data.create_id === patchCreateIdRef.current) {
        setPatchProgress(data.percentage);
        setPatchMessage(data.message);
      }
    });
    socket.on('xdelta_create_complete', (data) => {
      if (patchCreateIdRef.current && data.create_id === patchCreateIdRef.current) {
        setPatchProgress(100);
        setPatchResult(data);
        setPatchComplete(true);
        setCreatingPatch(false);
      }
    });
    socket.on('xdelta_create_error', (data) => {
      if (patchCreateIdRef.current && data.create_id === patchCreateIdRef.current) {
        setPatchError(data.error);
        setCreatingPatch(false);
      }
    });

    // bundle
    socket.on('bundle_export_progress', (data) => {
      if (bundleExportIdRef.current && data.export_id === bundleExportIdRef.current) {
        setBundleProgress(data.percentage);
        setBundleMessage(data.message);
      }
    });
    socket.on('bundle_export_complete', (data) => {
      if (bundleExportIdRef.current && data.export_id === bundleExportIdRef.current) {
        setBundleProgress(100);
        setBundleComplete(true);
        setBundleExporting(false);
        setBundleResult(data);
        playSound('achievement');
      }
    });
    socket.on('bundle_export_error', (data) => {
      if (bundleExportIdRef.current && data.export_id === bundleExportIdRef.current) {
        setBundleError(data.error);
        setBundleExporting(false);
        playSound('error');
      }
    });

    // test in game
    socket.on('test_progress', (data) => {
      setTestStage(data.stage || '');
      setTestProgress(data.percentage || 0);
      setTestMessage(data.message || 'Testing…');
    });
    socket.on('test_complete', (data) => {
      setTesting(false);
      setTestResult(data);
      playSound(data.success ? 'achievement' : 'error');
    });
    socket.on('test_error', (data) => {
      setTesting(false);
      setTestError(data.error);
      playSound('error');
    });

    return () => socket.disconnect();
  }, []);

  // recommended compression on mount
  useEffect(() => {
    fetch(`${API_URL}/recommended-compression`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setRecommendedCompression(data.ratio);
          setCostumeCount(data.addedCostumes);
        }
      })
      .catch((err) => console.error('Failed to fetch recommended compression:', err));
  }, []);

  // ---- export start ----
  const handleStartExport = async ({ useTexturePack = false, compressionOverride = null, colorSmashOverride = null } = {}) => {
    playSound('start');
    setPhase('exporting');
    setProgress(0);
    setMessage('Starting export...');
    setError(null);
    setAutoResult(null);
    setAutoError(null);
    setCharacters([]);

    const finalCompression = compressionOverride !== null ? compressionOverride : cspCompression;
    const finalColorSmash = colorSmashOverride !== null ? colorSmashOverride : useColorSmash;

    try {
      const response = await fetch(`${API_URL}/export/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          cspCompression: finalCompression,
          useColorSmash: finalColorSmash,
          texturePackMode: useTexturePack,
          slippiDolphinPath: useTexturePack ? slippiDolphinPath : null,
        }),
      });
      const data = await response.json();
      if (!data.success) {
        playSound('error');
        setError(data.error);
        setPhase('error');
      } else if (data.buildId) {
        setBuildId(data.buildId);
      }
    } catch (err) {
      playSound('error');
      setError(`Failed to start export: ${err.message}`);
      setPhase('error');
    }
  };

  const handleQuickExport = () => {
    textureModeRef.current = 'auto';
    handleStartExport({ useTexturePack: false, compressionOverride: recommendedCompression, colorSmashOverride: false });
  };
  const handleTexturePackExport = (mode = 'auto') => {
    textureModeRef.current = mode;
    handleStartExport({ useTexturePack: true, compressionOverride: 1.0, colorSmashOverride: false });
  };
  const handleAdvancedExport = () => {
    textureModeRef.current = 'auto';
    handleStartExport({ useTexturePack: false, compressionOverride: cspCompression, colorSmashOverride: useColorSmash });
  };

  // ---- manual scan controls ----
  const handleStopListening = async () => {
    try {
      const response = await fetch(`${API_URL}/texture-pack/stop-listening`, { method: 'POST' });
      const data = await response.json();
      if (data.success && data.texturePackPath) setTexturePackPath(data.texturePackPath);
    } catch (err) {
      console.error('Failed to stop listening:', err);
    }
    setPhase('done');
  };

  // ---- close ----
  const handleClose = async () => {
    playSound('back');
    if (phase === 'listening') {
      try {
        await fetch(`${API_URL}/texture-pack/stop-listening`, { method: 'POST' });
      } catch (err) {
        /* best effort */
      }
    }
    onClose();
  };

  // ---- download ----
  const handleDownload = () => {
    playSound('start');
    const link = document.createElement('a');
    link.href = `${API_URL}/export/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ---- bundle ----
  const vanillaIsoPath = () => localStorage.getItem('vanilla_iso_path');
  const handleShowBundleForm = () => {
    setBundleName(projectName || 'My Mod Pack');
    setBundleDescription('');
    setBundleImage(null);
    setBundleImagePreview(null);
    setShowBundleForm(true);
    setPhase('done');
    playSound('select');
  };
  const handleBundleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setBundleImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setBundleImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };
  const handleStartBundleExport = async () => {
    const vanilla = vanillaIsoPath();
    if (!vanilla) return; // form disables submit, but guard anyway
    if (!bundleName.trim()) return;

    setShowBundleForm(false);
    setBundleExporting(true);
    setBundleProgress(0);
    setBundleMessage('Creating bundle...');
    setBundleError(null);
    setBundleComplete(false);
    setBundleResult(null);
    playSound('start');

    try {
      const formData = new FormData();
      formData.append('name', bundleName.trim());
      formData.append('description', bundleDescription.trim());
      formData.append('buildName', buildId || bundleName.trim().toLowerCase().replace(/\s+/g, '-'));
      formData.append('vanillaIsoPath', vanilla);
      formData.append('exportedIsoPath', exportedIsoPath);
      if (texturePackPath) formData.append('texturePackPath', texturePackPath);
      if (bundleImage) formData.append('image', bundleImage);

      const response = await fetch(`${API_URL}/bundle/export`, { method: 'POST', body: formData });
      const data = await response.json();
      if (data.success) {
        bundleExportIdRef.current = data.export_id;
      } else {
        setBundleError(data.error);
        setBundleExporting(false);
        playSound('error');
      }
    } catch (err) {
      setBundleError(`Export error: ${err.message}`);
      setBundleExporting(false);
      playSound('error');
    }
  };
  const handleDownloadBundle = () => {
    if (!bundleResult?.bundle_id) return;
    playSound('start');
    const link = document.createElement('a');
    link.href = `${API_URL}/bundle/download/${bundleResult.bundle_id}`;
    link.download = bundleResult.filename || 'bundle.ssbm';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ---- patch ----
  const handleStartCreatePatch = async () => {
    if (!patchName.trim()) return;
    const vanilla = vanillaIsoPath();
    if (!vanilla) {
      setPatchError('No vanilla ISO path set. Set it in Settings first.');
      return;
    }
    if (!exportedIsoPath) {
      setPatchError('No exported ISO path available.');
      return;
    }
    setCreatingPatch(true);
    setPatchProgress(0);
    setPatchMessage('Starting...');
    setPatchError(null);
    setPatchComplete(false);
    setPatchResult(null);
    try {
      const response = await fetch(`${API_URL}/xdelta/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vanillaIsoPath: vanilla, moddedIsoPath: exportedIsoPath, name: patchName, description: patchDescription }),
      });
      const data = await response.json();
      if (data.success) {
        patchCreateIdRef.current = data.create_id;
      } else {
        setPatchError(data.error);
        setCreatingPatch(false);
      }
    } catch (err) {
      setPatchError(err.message);
      setCreatingPatch(false);
    }
  };
  const handleDownloadPatch = () => {
    if (!patchResult?.patch_id) return;
    const link = document.createElement('a');
    link.href = `${API_URL}/xdelta/download-patch/${patchResult.patch_id}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ---- test ----
  const handleTestInGame = async () => {
    playSound('start');
    setTesting(true);
    setTestProgress(0);
    setTestStage('starting');
    setTestMessage('Starting in-game test…');
    setTestResult(null);
    setTestError(null);
    try {
      const body = { isoPath: exportedIsoPath, slippiDolphinPath };
      if (testManifestPath.trim()) body.manifestPath = testManifestPath.trim();
      const response = await fetch(`${API_URL}/test-in-game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!data.success) {
        setTesting(false);
        setTestError(data.error || 'Failed to start test');
        playSound('error');
      }
    } catch (err) {
      setTesting(false);
      setTestError(`Failed to start test: ${err.message}`);
      playSound('error');
    }
  };

  const canBundle = usedTexturePack && !!texturePackPath;

  // ---- render the post-export "what next" screen ----
  const renderDone = () => {
    if (creatingPatch) {
      return (
        <ProgressPanel
          title="Creating Patch..."
          label="Patch creation progress"
          progressValue={patchProgress > 0 ? patchProgress : null}
          messageText={getProgressMessage(patchMessage, 'Comparing ISOs...')}
        />
      );
    }
    if (patchComplete && patchResult) {
      return (
        <div className="export-complete">
          <div className="success-icon">✓</div>
          <h3>Patch Created!</h3>
          <p>Your patch "{patchResult.name}" has been saved.</p>
          <p className="subtle-line">
            Size: {patchResult.size_mb} MB
            {patchResult.size_mb < 25 && <span className="discord-ok"> (Discord-friendly!)</span>}
          </p>
          <div className="complete-actions">
            <button className="btn-download" onClick={handleDownloadPatch}>Download Patch</button>
            <button className="btn-download btn-gold" onClick={handleDownload}>Download ISO</button>
            <button className="btn-secondary" onClick={handleClose}>Close</button>
          </div>
        </div>
      );
    }
    if (patchError) {
      return (
        <div className="export-error">
          <div className="error-icon">✕</div>
          <h3>Patch Creation Failed</h3>
          <p className="error-message">{patchError}</p>
          <div className="complete-actions">
            <button className="btn-download" onClick={handleDownload}>Download ISO Anyway</button>
            <button className="btn-secondary" onClick={() => setPatchError(null)}>Back</button>
          </div>
        </div>
      );
    }
    if (bundleExporting) {
      return (
        <ProgressPanel
          title="Creating Bundle..."
          label="Bundle export progress"
          progressValue={bundleProgress > 0 ? bundleProgress : null}
          messageText={getProgressMessage(bundleMessage, 'Preparing bundle assets...')}
        />
      );
    }
    if (bundleComplete && bundleResult) {
      return (
        <div className="export-complete">
          <div className="success-icon">✓</div>
          <h3>Bundle Created!</h3>
          <p className="subtle-line">{bundleResult.filename}</p>
          <p className="subtle-line">
            Size: {bundleResult.size_mb} MB
            {bundleResult.texture_count > 0 && ` • ${bundleResult.texture_count} textures`}
          </p>
          <p className="share-note">Share this file — friends can install it with one click!</p>
          <div className="complete-actions">
            <button className="btn-download btn-gold" onClick={handleDownloadBundle}>Download Bundle</button>
            <button className="btn-secondary" onClick={handleClose}>Done</button>
          </div>
        </div>
      );
    }
    if (bundleError) {
      return (
        <div className="export-error">
          <div className="error-icon">✕</div>
          <h3>Bundle Export Failed</h3>
          <p className="error-message">{bundleError}</p>
          <div className="complete-actions">
            <button className="btn-download" onClick={handleDownload}>Download ISO Anyway</button>
            <button className="btn-secondary" onClick={() => setBundleError(null)}>Back</button>
          </div>
        </div>
      );
    }
    if (showBundleForm) {
      return (
        <BundleForm
          bundleName={bundleName}
          setBundleName={setBundleName}
          bundleDescription={bundleDescription}
          setBundleDescription={setBundleDescription}
          bundleImagePreview={bundleImagePreview}
          onImageChange={handleBundleImageChange}
          onRemoveImage={() => { setBundleImage(null); setBundleImagePreview(null); }}
          onSubmit={handleStartBundleExport}
          onCancel={() => setShowBundleForm(false)}
          vanillaMissing={!vanillaIsoPath()}
        />
      );
    }

    // Default: success + chained actions
    return (
      <div className="export-complete export-done">
        <div className="success-icon">✓</div>
        <h3>Export Complete!</h3>
        <p>Your modified ISO is ready to download.</p>
        {canBundle && (
          <p className="auto-applied-summary">
            HD texture pack applied to your Slippi Load folder — it’ll show next boot.
          </p>
        )}
        <div className="complete-actions">
          <button className="btn-download" onClick={handleDownload}>Download {filename}</button>
          <button className="btn-secondary" onClick={handleClose}>Close</button>
        </div>

        <div className="action-section">
          <TestInGamePanel
            testing={testing}
            testProgress={testProgress}
            testStage={testStage}
            testMessage={testMessage}
            testResult={testResult}
            testError={testError}
            slippiPath={slippiDolphinPath}
            manifestPath={testManifestPath}
            setManifestPath={setTestManifestPath}
            showTestAdvanced={showTestAdvanced}
            setShowTestAdvanced={setShowTestAdvanced}
            onTest={handleTestInGame}
          />
        </div>

        <div className="action-section">
          {!showPatchForm ? (
            <>
              <h4 className="action-heading">Create shareable patch</h4>
              <p className="action-blurb">
                A small <code>.xdelta</code> file others apply to their vanilla ISO to recreate this build.
              </p>
              <button className="btn-secondary full" onClick={() => setShowPatchForm(true)}>
                Create Patch
              </button>
            </>
          ) : (
            <div className="patch-form">
              <h4 className="action-heading">Create Patch</h4>
              <div className="form-field">
                <label>Patch Name</label>
                <input type="text" value={patchName} onChange={(e) => setPatchName(e.target.value)} placeholder="My Awesome Mod Pack" />
              </div>
              <div className="form-field">
                <label>Description (optional)</label>
                <textarea value={patchDescription} onChange={(e) => setPatchDescription(e.target.value)} placeholder="Describe what's in this patch..." rows={2} />
              </div>
              <div className="form-actions">
                <button className="btn-export" onClick={handleStartCreatePatch} disabled={!patchName.trim()}>Create Patch</button>
                <button className="btn-secondary" onClick={() => setShowPatchForm(false)}>Cancel</button>
              </div>
            </div>
          )}
        </div>

        {canBundle && (
          <div className="action-section">
            <h4 className="action-heading">Export as bundle</h4>
            <p className="action-blurb">
              A <code>.ssbm</code> file (patch + texture pack) friends install in one click.
            </p>
            <button className="btn-download btn-gold full" onClick={handleShowBundleForm}>
              Export Bundle
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Export Project</h2>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          {phase === 'choose' && (
            <ExportModePicker
              filename={filename}
              setFilename={setFilename}
              recommendedCompression={recommendedCompression}
              costumeCount={costumeCount}
              slippiPath={slippiDolphinPath}
              cspCompression={cspCompression}
              setCspCompression={setCspCompression}
              useColorSmash={useColorSmash}
              setUseColorSmash={setUseColorSmash}
              showAdvanced={showAdvanced}
              setShowAdvanced={setShowAdvanced}
              onQuickExport={handleQuickExport}
              onTexturePackExport={handleTexturePackExport}
              onAdvancedExport={handleAdvancedExport}
            />
          )}

          {phase === 'exporting' && (
            <ProgressPanel
              title="Exporting ISO..."
              label="ISO export progress"
              progressValue={progress > 0 ? progress : null}
              messageText={getProgressMessage(message, 'Preparing export pipeline...')}
            />
          )}

          {phase === 'autoTexture' && (
            <AutoTexturePanel
              progress={autoProgress}
              result={autoResult}
              error={autoError}
              onContinue={() => setPhase('done')}
              onManualFallback={() => startManualListening(buildId)}
              onRetry={() => startAutoTexture(buildId)}
            />
          )}

          {phase === 'listening' && (
            <ManualListenPanel
              textureProgress={textureProgress}
              characters={characters}
              currentCharIndex={currentCharIndex}
              setCurrentCharIndex={setCurrentCharIndex}
              onDownload={handleDownload}
              onDone={handleStopListening}
              onShowBundle={async () => { await handleStopListening(); handleShowBundleForm(); }}
            />
          )}

          {phase === 'done' && renderDone()}

          {phase === 'error' && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Export Failed</h3>
              <p className="error-message">{error}</p>
              <button className="btn-secondary" onClick={handleClose}>Close</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IsoBuilder;
