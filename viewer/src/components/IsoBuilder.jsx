import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { playSound } from '../utils/sounds';
import { API_URL, BACKEND_URL } from '../config';
import { getProgressMessage } from './shared/progressText';
import ProgressPanel from './export/ProgressPanel';
import ExportHome from './export/ExportHome';
import './IsoBuilder.css';

// Minimalist export flow. Three one-shot pipelines run start-to-finish with no
// post-export menus:
//   iso    : build ISO -> done
//   patch  : build ISO -> xdelta patch -> done
//   bundle : build texture-pack ISO -> auto-apply HD textures -> .ssbm in vault
//
// phase: home | working | done | error
const IsoBuilder = ({ onClose, projectName = 'game' }) => {
  const getDefaultName = () => {
    const now = new Date();
    const date = now.toISOString().slice(0, 10);
    const time = now.toTimeString().slice(0, 5).replace(':', '-');
    return `${projectName}_${date}_${time}`;
  };

  const [phase, setPhase] = useState('home');
  const [action, setAction] = useState(null); // iso | patch | bundle
  const [error, setError] = useState(null);

  // The name box edits a base name (no extension); ".iso" is appended on save.
  const [baseName, setBaseName] = useState(getDefaultName());
  const filename = `${baseName.trim() || 'game'}.iso`;
  const [cspCompression, setCspCompression] = useState(1.0);
  const [useColorSmash, setUseColorSmash] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [recommendedCompression, setRecommendedCompression] = useState(1.0);

  // unified working-panel state
  const [progress, setProgress] = useState(0);
  const [progressTitle, setProgressTitle] = useState('Working…');
  const [stepMeta, setStepMeta] = useState(null);
  const [message, setMessage] = useState('');

  // results
  const [patchResult, setPatchResult] = useState(null);
  const [bundleResult, setBundleResult] = useState(null);

  // settings paths (read once)
  const [slippiDolphinPath] = useState(() => localStorage.getItem('slippi_dolphin_path') || '');
  const [vanillaIsoPath] = useState(() => localStorage.getItem('vanilla_iso_path') || '');

  // values the chained socket steps need, kept on refs to dodge stale closures
  const actionRef = useRef(null);
  const exportedIsoPathRef = useRef(null);
  const buildIdRef = useRef(null);
  const patchCreateIdRef = useRef(null);
  const bundleExportIdRef = useRef(null);
  const liveRef = useRef({});

  const bundleName = () => filename.replace(/\.iso$/i, '');

  // ---- chained pipeline steps (reassigned each render so refs stay fresh) ----
  const startPatch = async (isoPath) => {
    setProgressTitle('Creating patch…');
    setStepMeta('Step 2 of 2');
    setProgress(0);
    setMessage('Comparing ISOs…');
    try {
      const res = await fetch(`${API_URL}/xdelta/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vanillaIsoPath,
          moddedIsoPath: isoPath,
          name: bundleName(),
          description: '',
        }),
      });
      const data = await res.json();
      if (data.success) patchCreateIdRef.current = data.create_id;
      else fail(data.error || 'Failed to create patch');
    } catch (err) {
      fail(`Failed to create patch: ${err.message}`);
    }
  };

  const startAutoTexture = async (bId) => {
    setProgressTitle('Applying HD texture pack…');
    setStepMeta('Step 2 of 3');
    setProgress(0);
    setMessage('Computing portrait names…');
    try {
      const res = await fetch(`${API_URL}/texture-pack/auto-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ buildId: bId, slippiPath: slippiDolphinPath }),
      });
      const data = await res.json();
      if (!data.success) fail(data.error || 'Failed to start texture pack');
    } catch (err) {
      fail(`Failed to apply texture pack: ${err.message}`);
    }
  };

  const startBundlePackage = async (texturePackPath) => {
    setProgressTitle('Packaging bundle…');
    setStepMeta('Step 3 of 3');
    setProgress(0);
    setMessage('Building patch + bundle…');
    try {
      const formData = new FormData();
      formData.append('name', bundleName());
      formData.append('description', '');
      formData.append('buildName', buildIdRef.current || bundleName());
      formData.append('vanillaIsoPath', vanillaIsoPath);
      formData.append('exportedIsoPath', exportedIsoPathRef.current);
      if (texturePackPath) formData.append('texturePackPath', texturePackPath);
      const res = await fetch(`${API_URL}/bundle/export`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.success) bundleExportIdRef.current = data.export_id;
      else fail(data.error || 'Failed to create bundle');
    } catch (err) {
      fail(`Failed to create bundle: ${err.message}`);
    }
  };

  const fail = (msg) => {
    playSound('error');
    setError(msg);
    setPhase('error');
  };

  liveRef.current = { startPatch, startAutoTexture, startBundlePackage, fail };

  // ---- WebSocket wiring (connect once) ----
  useEffect(() => {
    const socket = io(BACKEND_URL);

    socket.on('export_progress', (data) => {
      setProgress(data.percentage);
      setMessage(data.message || 'Exporting assets…');
    });

    socket.on('export_complete', (data) => {
      setProgress(100);
      exportedIsoPathRef.current = data.path;
      const a = actionRef.current;
      if (a === 'iso') {
        playSound('achievement');
        setPhase('done');
      } else if (a === 'patch') {
        liveRef.current.startPatch(data.path);
      } else if (a === 'bundle') {
        buildIdRef.current = data.buildId;
        liveRef.current.startAutoTexture(data.buildId);
      }
    });

    socket.on('export_error', (data) => liveRef.current.fail(data.error));

    // auto texture pack (bundle step 2)
    socket.on('texture_auto_progress', (data) => {
      setProgress(data.percentage || 0);
      setMessage(data.message || 'Building texture pack…');
    });
    socket.on('texture_auto_complete', (data) => {
      liveRef.current.startBundlePackage(data.texturePackPath);
    });
    socket.on('texture_auto_error', (data) => liveRef.current.fail(data.error));

    // patch
    socket.on('xdelta_create_progress', (data) => {
      if (data.create_id === patchCreateIdRef.current) {
        setProgress(data.percentage);
        setMessage(data.message);
      }
    });
    socket.on('xdelta_create_complete', (data) => {
      if (data.create_id === patchCreateIdRef.current) {
        setProgress(100);
        setPatchResult(data);
        playSound('achievement');
        setPhase('done');
      }
    });
    socket.on('xdelta_create_error', (data) => {
      if (data.create_id === patchCreateIdRef.current) liveRef.current.fail(data.error);
    });

    // bundle (vault)
    socket.on('bundle_export_progress', (data) => {
      if (data.export_id === bundleExportIdRef.current) {
        setProgress(data.percentage);
        setMessage(data.message);
      }
    });
    socket.on('bundle_export_complete', (data) => {
      if (data.export_id === bundleExportIdRef.current) {
        setProgress(100);
        setBundleResult(data);
        playSound('achievement');
        setPhase('done');
      }
    });
    socket.on('bundle_export_error', (data) => {
      if (data.export_id === bundleExportIdRef.current) liveRef.current.fail(data.error);
    });

    return () => socket.disconnect();
  }, []);

  // recommended compression on mount -> seed the slider value
  useEffect(() => {
    fetch(`${API_URL}/recommended-compression`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setRecommendedCompression(data.ratio);
          setCspCompression(data.ratio);
        }
      })
      .catch((err) => console.error('Failed to fetch recommended compression:', err));
  }, []);

  // ---- kick off a pipeline ----
  const runExport = async ({ act, useTexturePack }) => {
    actionRef.current = act;
    setAction(act);
    playSound('start');
    setError(null);
    setPatchResult(null);
    setBundleResult(null);
    setProgress(0);
    setMessage('Starting…');
    setProgressTitle(useTexturePack ? 'Building texture-pack ISO…' : 'Building ISO…');
    setStepMeta(act === 'bundle' ? 'Step 1 of 3' : act === 'patch' ? 'Step 1 of 2' : null);
    setPhase('working');

    try {
      const res = await fetch(`${API_URL}/export/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          cspCompression,
          useColorSmash,
          texturePackMode: useTexturePack,
          slippiDolphinPath: useTexturePack ? slippiDolphinPath : null,
        }),
      });
      const data = await res.json();
      if (!data.success) fail(data.error || 'Failed to start export');
      else if (data.buildId) buildIdRef.current = data.buildId;
    } catch (err) {
      fail(`Failed to start export: ${err.message}`);
    }
  };

  const onExportIso = () => runExport({ act: 'iso', useTexturePack: false });
  const onExportPatch = () => runExport({ act: 'patch', useTexturePack: false });
  const onAddBundle = () => runExport({ act: 'bundle', useTexturePack: true });

  const handleClose = () => {
    playSound('back');
    onClose();
  };

  const handleDownload = () => {
    playSound('start');
    const link = document.createElement('a');
    link.href = `${API_URL}/export/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadPatch = () => {
    if (!patchResult?.patch_id) return;
    const link = document.createElement('a');
    link.href = `${API_URL}/xdelta/download-patch/${patchResult.patch_id}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

  // ---- done screens ----
  const renderDone = () => {
    if (action === 'patch' && patchResult) {
      return (
        <div className="export-complete">
          <div className="success-icon">✓</div>
          <h3>Patch Created</h3>
          <p className="subtle-line">
            {patchResult.size_mb} MB
            {patchResult.size_mb < 25 && <span className="discord-ok"> · Discord-friendly</span>}
            {' · saved to your Patches library'}
          </p>
          <div className="complete-actions">
            <button className="btn-download" onClick={handleDownloadPatch}>Download Patch</button>
            <button className="btn-secondary" onClick={handleClose}>Done</button>
          </div>
        </div>
      );
    }
    if (action === 'bundle' && bundleResult) {
      return (
        <div className="export-complete">
          <div className="success-icon">✓</div>
          <h3>Bundle Added</h3>
          <p className="subtle-line">
            “{bundleName()}” · {bundleResult.size_mb} MB
            {bundleResult.texture_count > 0 && ` · ${bundleResult.texture_count} HD portraits`}
          </p>
          <p className="share-note">
            Find it under <strong>Patches → Bundles</strong>. Rename it or add a cover there.
          </p>
          <div className="complete-actions">
            <button className="btn-download btn-gold" onClick={handleDownloadBundle}>Download</button>
            <button className="btn-secondary" onClick={handleClose}>Done</button>
          </div>
        </div>
      );
    }
    // iso
    return (
      <div className="export-complete">
        <div className="success-icon">✓</div>
        <h3>ISO Ready</h3>
        <p>Your modified ISO is ready to download.</p>
        <div className="complete-actions">
          <button className="btn-download" onClick={handleDownload}>Download {filename}</button>
          <button className="btn-secondary" onClick={handleClose}>Done</button>
        </div>
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
          {phase === 'home' && (
            <ExportHome
              name={baseName}
              setName={setBaseName}
              recommendedCompression={recommendedCompression}
              slippiPath={slippiDolphinPath}
              vanillaPath={vanillaIsoPath}
              cspCompression={cspCompression}
              setCspCompression={setCspCompression}
              useColorSmash={useColorSmash}
              setUseColorSmash={setUseColorSmash}
              showAdvanced={showAdvanced}
              setShowAdvanced={setShowAdvanced}
              onExportIso={onExportIso}
              onExportPatch={onExportPatch}
              onAddBundle={onAddBundle}
            />
          )}

          {phase === 'working' && (
            <ProgressPanel
              title={progressTitle}
              label="Export progress"
              progressValue={progress > 0 ? progress : null}
              metaText={stepMeta}
              messageText={getProgressMessage(message, 'Preparing…')}
            />
          )}

          {phase === 'done' && renderDone()}

          {phase === 'error' && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Export Failed</h3>
              <p className="error-message">{error}</p>
              <div className="complete-actions">
                {exportedIsoPathRef.current && (
                  <button className="btn-download" onClick={handleDownload}>Download ISO Anyway</button>
                )}
                <button className="btn-secondary" onClick={handleClose}>Close</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IsoBuilder;
