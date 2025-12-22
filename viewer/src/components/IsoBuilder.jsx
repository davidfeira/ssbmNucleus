import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import './IsoBuilder.css';

const IsoBuilder = ({ onClose }) => {
  const [filename, setFilename] = useState(`game_${new Date().toISOString().slice(0, 10)}.iso`);
  const [cspCompression, setCspCompression] = useState(1.0);
  const [useColorSmash, setUseColorSmash] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState(null);
  const [socket, setSocket] = useState(null);
  const [exportedIsoPath, setExportedIsoPath] = useState(null);

  // Patch creation state
  const [showPatchForm, setShowPatchForm] = useState(false);
  const [patchName, setPatchName] = useState('');
  const [patchDescription, setPatchDescription] = useState('');
  const [creatingPatch, setCreatingPatch] = useState(false);
  const [patchProgress, setPatchProgress] = useState(0);
  const [patchMessage, setPatchMessage] = useState('');
  const [patchComplete, setPatchComplete] = useState(false);
  const [patchError, setPatchError] = useState(null);
  const [patchResult, setPatchResult] = useState(null);
  const [patchCreateId, setPatchCreateId] = useState(null);

  const API_URL = 'http://127.0.0.1:5000';

  useEffect(() => {
    // Connect to WebSocket for progress updates
    const newSocket = io(API_URL);

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket');
    });

    newSocket.on('export_progress', (data) => {
      setProgress(data.percentage);
      setMessage(data.message || `Exporting... ${data.percentage}%`);
    });

    newSocket.on('export_complete', (data) => {
      setProgress(100);
      setMessage('Export complete!');
      setComplete(true);
      setExporting(false);
      setExportedIsoPath(data.path);
    });

    newSocket.on('export_error', (data) => {
      setError(data.error);
      setExporting(false);
    });

    // Patch creation events
    newSocket.on('xdelta_create_progress', (data) => {
      if (patchCreateId && data.create_id === patchCreateId) {
        setPatchProgress(data.percentage);
        setPatchMessage(data.message);
      }
    });

    newSocket.on('xdelta_create_complete', (data) => {
      if (patchCreateId && data.create_id === patchCreateId) {
        setPatchProgress(100);
        setPatchResult(data);
        setPatchComplete(true);
        setCreatingPatch(false);
      }
    });

    newSocket.on('xdelta_create_error', (data) => {
      if (patchCreateId && data.create_id === patchCreateId) {
        setPatchError(data.error);
        setCreatingPatch(false);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [patchCreateId]);

  const handleStartExport = async () => {
    setExporting(true);
    setProgress(0);
    setMessage('Starting export...');
    setError(null);
    setComplete(false);

    try {
      const response = await fetch(`${API_URL}/api/mex/export/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename,
          cspCompression,
          useColorSmash
        })
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.error);
        setExporting(false);
      }
    } catch (err) {
      setError(`Failed to start export: ${err.message}`);
      setExporting(false);
    }
  };

  const handleDownload = () => {
    // Create a temporary anchor element to trigger download without opening new window
    const link = document.createElement('a');
    link.href = `${API_URL}/api/mex/export/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleStartCreatePatch = async () => {
    if (!patchName.trim()) {
      alert('Please enter a name for the patch');
      return;
    }

    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path');
    if (!vanillaIsoPath) {
      alert('No vanilla ISO path set. Please set it in Settings first.');
      return;
    }

    if (!exportedIsoPath) {
      alert('No exported ISO path available');
      return;
    }

    setCreatingPatch(true);
    setPatchProgress(0);
    setPatchMessage('Starting...');
    setPatchError(null);
    setPatchComplete(false);
    setPatchResult(null);

    try {
      const response = await fetch(`${API_URL}/api/mex/xdelta/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vanillaIsoPath,
          moddedIsoPath: exportedIsoPath,
          name: patchName,
          description: patchDescription
        })
      });

      const data = await response.json();

      if (data.success) {
        setPatchCreateId(data.create_id);
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
    link.href = `${API_URL}/api/mex/xdelta/download-patch/${patchResult.patch_id}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Export ISO</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {!exporting && !complete && !error && (
            <>
              <div className="form-group">
                <label htmlFor="compression">
                  CSP Compression
                </label>
                <div className="compression-input-group">
                  <input
                    type="number"
                    id="compression-input"
                    min="0.1"
                    max="1.0"
                    step="0.01"
                    value={cspCompression}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val) && val >= 0.1 && val <= 1.0) {
                        setCspCompression(val);
                      }
                    }}
                    className="compression-number-input"
                  />
                  <span className="compression-multiplier">x</span>
                </div>
                <input
                  type="range"
                  id="compression"
                  min="0.1"
                  max="1.0"
                  step="0.01"
                  value={cspCompression}
                  onChange={(e) => setCspCompression(parseFloat(e.target.value))}
                  className="compression-slider"
                />
                <div className="compression-hints">
                  <span className="hint-label">0.1 (Tiny)</span>
                  <span className="hint-label">1.0 (Full)</span>
                </div>
                <p className="compression-info">
                  Melee can crash if there are too many images. Try reducing the compression ratio to free up more memory.
                </p>
              </div>

              <div className="form-group color-smash-group">
                <label className="color-smash-label">
                  <input
                    type="checkbox"
                    checked={useColorSmash}
                    onChange={(e) => setUseColorSmash(e.target.checked)}
                    className="color-smash-checkbox"
                  />
                  <span>Enable Color Smash</span>
                </label>
                <p className="color-smash-info">
                  Can save a lot of memory, but produces artifacts/compression.
                </p>
              </div>

              <div className="warning-box">
                <p><strong>Note:</strong> This can take a few minutes.</p>
              </div>

              <button
                className="btn-export"
                onClick={handleStartExport}
              >
                Start Export
              </button>
            </>
          )}

          {exporting && (
            <div className="export-progress">
              <div className="progress-header">
                <h3>Exporting ISO...</h3>
                <span className="progress-percentage">{progress}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              <p className="progress-message">{message}</p>

              <div className="export-spinner">
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {complete && !creatingPatch && !patchComplete && !patchError && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Export Complete!</h3>
              <p>Your modified ISO is ready to download.</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download {filename}
                </button>
                <button className="btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>

              {/* Patch Creation Section */}
              <div className="patch-creation-section" style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
                {!showPatchForm ? (
                  <button
                    className="btn-secondary"
                    onClick={() => setShowPatchForm(true)}
                    style={{ width: '100%' }}
                  >
                    Create Shareable Patch
                  </button>
                ) : (
                  <div className="patch-form">
                    <h4 style={{ marginBottom: '1rem', color: 'var(--color-text-primary)' }}>Create Patch</h4>
                    <p style={{ fontSize: '0.9em', color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
                      Create a small patch file that others can use to recreate this ISO.
                    </p>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em' }}>Patch Name</label>
                      <input
                        type="text"
                        value={patchName}
                        onChange={(e) => setPatchName(e.target.value)}
                        placeholder="My Awesome Mod Pack"
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-border)',
                          background: 'var(--color-bg-surface)',
                          color: 'var(--color-text-primary)'
                        }}
                      />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em' }}>Description (optional)</label>
                      <textarea
                        value={patchDescription}
                        onChange={(e) => setPatchDescription(e.target.value)}
                        placeholder="Describe what's in this patch..."
                        rows={2}
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-border)',
                          background: 'var(--color-bg-surface)',
                          color: 'var(--color-text-primary)',
                          resize: 'vertical'
                        }}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn-export"
                        onClick={handleStartCreatePatch}
                        disabled={!patchName.trim()}
                        style={{ flex: 1 }}
                      >
                        Create Patch
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => setShowPatchForm(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {creatingPatch && (
            <div className="export-progress" style={{ textAlign: 'center' }}>
              <div className="export-spinner">
                <div className="spinner"></div>
              </div>

              <h3 style={{ marginTop: '1rem' }}>Creating Patch...</h3>

              <p className="progress-message">
                {patchMessage || 'Comparing ISOs...'}
              </p>
            </div>
          )}

          {patchComplete && patchResult && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Patch Created!</h3>
              <p>Your patch "{patchResult.name}" has been created and saved.</p>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9em' }}>
                Size: {patchResult.size_mb} MB
                {patchResult.size_mb < 25 && (
                  <span style={{ color: 'var(--color-success)', marginLeft: '0.5rem' }}>
                    (Discord-friendly!)
                  </span>
                )}
              </p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownloadPatch}>
                  Download Patch
                </button>
                <button className="btn-download" onClick={handleDownload} style={{ background: 'var(--gradient-gold)' }}>
                  Download ISO
                </button>
                <button className="btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>
            </div>
          )}

          {patchError && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Patch Creation Failed</h3>
              <p className="error-message">{patchError}</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download ISO Anyway
                </button>
                <button className="btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Export Failed</h3>
              <p className="error-message">{error}</p>
              <button className="btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IsoBuilder;
