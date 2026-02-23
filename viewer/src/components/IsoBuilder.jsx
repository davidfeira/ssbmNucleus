import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { playSound } from '../utils/sounds';
import { API_URL, BACKEND_URL } from '../config';
import './IsoBuilder.css';

// CSS screen order for scanning - matches the character select screen layout
// Sheik is at the end since she shares Zelda's CSP slot
const CSS_SCAN_ORDER = [
  'Dr. Mario', 'Mario', 'Luigi', 'Bowser', 'Peach', 'Yoshi',
  'Donkey Kong', 'Captain Falcon', 'Ganondorf', 'Young Link', 'Link', 'Zelda',
  'Samus', 'Kirby', 'Ice Climbers', 'Ness', 'Fox', 'Falco',
  'Pichu', 'Pikachu', 'Jigglypuff', 'Mewtwo', 'Mr. Game & Watch', 'Marth', 'Roy',
  'Sheik'
];

const IsoBuilder = ({ onClose, projectName = 'game' }) => {
  // Format: BUILDNAME_YYYY-MM-DD_HH-MM.iso
  const getDefaultFilename = () => {
    const now = new Date();
    const date = now.toISOString().slice(0, 10);
    const time = now.toTimeString().slice(0, 5).replace(':', '-');
    return `${projectName}_${date}_${time}.iso`;
  };
  const [filename, setFilename] = useState(getDefaultFilename());
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

  // Texture pack mode state
  const [listeningMode, setListeningMode] = useState(false);
  const [textureProgress, setTextureProgress] = useState({ matched: 0, total: 0, percentage: 0 });
  const [matchedTextures, setMatchedTextures] = useState([]);
  const [buildId, setBuildId] = useState(null);
  const [slippiDolphinPath, setSlippiDolphinPath] = useState(localStorage.getItem('slippi_dolphin_path') || '');
  const [characters, setCharacters] = useState([]);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [confirmedChars, setConfirmedChars] = useState(new Set());

  // New state for redesigned UI
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [recommendedCompression, setRecommendedCompression] = useState(1.0);
  const [costumeCount, setCostumeCount] = useState(0);

  // Bundle export state (inline, no separate modal)
  const [texturePackPath, setTexturePackPath] = useState(null);
  const [showBundleForm, setShowBundleForm] = useState(false);
  const [bundleName, setBundleName] = useState('');
  const [bundleDescription, setBundleDescription] = useState('');
  const [bundleImage, setBundleImage] = useState(null);
  const [bundleImagePreview, setBundleImagePreview] = useState(null);
  const [bundleExporting, setBundleExporting] = useState(false);
  const [bundleExportId, setBundleExportId] = useState(null);
  const [bundleProgress, setBundleProgress] = useState(0);
  const [bundleMessage, setBundleMessage] = useState('');
  const [bundleComplete, setBundleComplete] = useState(false);
  const [bundleError, setBundleError] = useState(null);
  const [bundleResult, setBundleResult] = useState(null);

  useEffect(() => {
    // Connect to WebSocket for progress updates
    const newSocket = io(BACKEND_URL);

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket');
    });

    newSocket.on('export_progress', (data) => {
      setProgress(data.percentage);
      setMessage(data.message || `Exporting... ${data.percentage}%`);
    });

    newSocket.on('export_complete', async (data) => {
      setProgress(100);
      setMessage('Export complete!');
      setComplete(true);
      setExporting(false);
      setExportedIsoPath(data.path);
      playSound('achievement');

      // If texture pack mode, start listening
      if (data.texturePackMode && data.buildId) {
        setBuildId(data.buildId);
        setTextureProgress({ matched: 0, total: data.totalCostumes, percentage: 0 });

        try {
          const response = await fetch(`${API_URL}/texture-pack/start-listening`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              buildId: data.buildId,
              slippiPath: localStorage.getItem('slippi_dolphin_path')
            })
          });

          const result = await response.json();
          if (result.success) {
            setListeningMode(true);
            const chars = result.characters || [];
            // Sort by CSS screen order for intuitive scanning
            const sortedChars = [...chars].sort((a, b) => {
              const aIdx = CSS_SCAN_ORDER.indexOf(a.name);
              const bIdx = CSS_SCAN_ORDER.indexOf(b.name);
              // Put unknown characters at the end
              if (aIdx === -1 && bIdx === -1) return a.name.localeCompare(b.name);
              if (aIdx === -1) return 1;
              if (bIdx === -1) return -1;
              return aIdx - bIdx;
            });
            const filteredTotal = sortedChars.reduce((sum, c) => sum + c.total, 0);
            setTextureProgress({ matched: 0, total: filteredTotal, percentage: 0 });
            setCharacters(sortedChars);
            setCurrentCharIndex(0);
            setConfirmedChars(new Set());
          }
        } catch (err) {
          console.error('Failed to start texture listening:', err);
        }
      }
    });

    // Texture pack events
    newSocket.on('texture_matched', (data) => {
      setMatchedTextures(prev => [...prev.slice(-9), data]); // Keep last 10

      // Update character progress and auto-advance
      setCharacters(prev => {
        const updated = prev.map(char => {
          if (char.name === data.character) {
            return {
              ...char,
              matched: char.matched + 1,
              costumes: char.costumes.map(c =>
                c.index === data.costumeIndex ? { ...c, matched: true } : c
              )
            };
          }
          return char;
        });

        // Auto-advance: find next character that still needs scanning
        const matchedCharIdx = updated.findIndex(c => c.name === data.character);
        const matchedChar = updated[matchedCharIdx];

        // If current character is now complete, find next incomplete one
        if (matchedChar && matchedChar.matched + 1 >= matchedChar.total) {
          const nextIncomplete = updated.findIndex(c => c.matched < c.total);
          if (nextIncomplete !== -1) {
            setCurrentCharIndex(nextIncomplete);
          }
        } else if (matchedCharIdx !== -1) {
          // Otherwise just show the character that got the match
          setCurrentCharIndex(matchedCharIdx);
        }

        return updated;
      });
    });

    newSocket.on('texture_progress', (data) => {
      setTextureProgress(data);
    });

    newSocket.on('export_error', (data) => {
      playSound('error');
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

    // Bundle export events
    newSocket.on('bundle_export_progress', (data) => {
      if (bundleExportId && data.export_id === bundleExportId) {
        setBundleProgress(data.percentage);
        setBundleMessage(data.message);
      }
    });

    newSocket.on('bundle_export_complete', (data) => {
      if (bundleExportId && data.export_id === bundleExportId) {
        setBundleProgress(100);
        setBundleComplete(true);
        setBundleExporting(false);
        setBundleResult(data);
        playSound('achievement');
      }
    });

    newSocket.on('bundle_export_error', (data) => {
      if (bundleExportId && data.export_id === bundleExportId) {
        setBundleError(data.error);
        setBundleExporting(false);
        playSound('error');
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [patchCreateId, bundleExportId]);

  // Fetch recommended compression on mount
  useEffect(() => {
    fetch(`${API_URL}/recommended-compression`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setRecommendedCompression(data.ratio);
          setCostumeCount(data.addedCostumes);
        }
      })
      .catch(err => console.error('Failed to fetch recommended compression:', err));
  }, []);

  const handleStartExport = async (options = {}) => {
    const {
      useTexturePack = false,
      compressionOverride = null,
      colorSmashOverride = null
    } = options;

    playSound('start');
    setExporting(true);
    setProgress(0);
    setMessage('Starting export...');
    setError(null);
    setComplete(false);
    setListeningMode(false);
    setMatchedTextures([]);

    // Determine compression: override > manual slider value
    const finalCompression = compressionOverride !== null ? compressionOverride : cspCompression;
    const finalColorSmash = colorSmashOverride !== null ? colorSmashOverride : useColorSmash;

    try {
      const response = await fetch(`${API_URL}/export/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename,
          cspCompression: finalCompression,
          useColorSmash: finalColorSmash,
          texturePackMode: useTexturePack,
          slippiDolphinPath: useTexturePack ? slippiDolphinPath : null
        })
      });

      const data = await response.json();

      if (!data.success) {
        playSound('error');
        setError(data.error);
        setExporting(false);
      } else if (data.buildId) {
        setBuildId(data.buildId);
      }
    } catch (err) {
      playSound('error');
      setError(`Failed to start export: ${err.message}`);
      setExporting(false);
    }
  };

  const handleQuickExport = () => {
    handleStartExport({
      useTexturePack: false,
      compressionOverride: recommendedCompression,
      colorSmashOverride: false
    });
  };

  const handleTexturePackExport = () => {
    handleStartExport({
      useTexturePack: true,
      compressionOverride: 1.0,
      colorSmashOverride: false
    });
  };

  const handleAdvancedExport = () => {
    handleStartExport({
      useTexturePack: false,
      compressionOverride: cspCompression,
      colorSmashOverride: useColorSmash
    });
  };

  const handleStopListening = async () => {
    try {
      const response = await fetch(`${API_URL}/texture-pack/stop-listening`, {
        method: 'POST'
      });

      const data = await response.json();
      if (data.success) {
        setListeningMode(false);
        // Save texture pack path for bundle export
        if (data.texturePackPath) {
          setTexturePackPath(data.texturePackPath);
        }
        // Show success message with path
        setMessage(`Texture pack created! ${data.matchedCount}/${data.totalCount} textures matched.`);
      }
    } catch (err) {
      console.error('Failed to stop listening:', err);
    }
  };

  // Handle modal close - cleanup texture listening if active
  const handleClose = async () => {
    playSound('back');
    if (listeningMode) {
      await handleStopListening();
    }
    onClose();
  };

  const handleDownload = () => {
    playSound('start');
    // Create a temporary anchor element to trigger download without opening new window
    const link = document.createElement('a');
    link.href = `${API_URL}/export/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleShowBundleForm = () => {
    // Initialize with project name
    setBundleName(projectName || 'My Mod Pack');
    setBundleDescription('');
    setBundleImage(null);
    setBundleImagePreview(null);
    setShowBundleForm(true);
    playSound('select');
  };

  const handleBundleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setBundleImage(file);
      // Create preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setBundleImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStartBundleExport = async () => {
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path');
    if (!vanillaIsoPath) {
      alert('Vanilla ISO path not set. Please configure it in Settings.');
      return;
    }

    if (!bundleName.trim()) {
      alert('Please enter a name for the bundle');
      return;
    }

    setShowBundleForm(false);
    setBundleExporting(true);
    setBundleProgress(0);
    setBundleMessage('Finalizing texture pack...');
    setBundleError(null);
    setBundleComplete(false);
    setBundleResult(null);
    playSound('start');

    try {
      // First, stop listening to finalize the texture pack and get the path
      let finalTexturePackPath = texturePackPath;
      if (listeningMode) {
        const stopResponse = await fetch(`${API_URL}/texture-pack/stop-listening`, {
          method: 'POST'
        });
        const stopData = await stopResponse.json();
        if (stopData.success && stopData.texturePackPath) {
          finalTexturePackPath = stopData.texturePackPath;
          setTexturePackPath(stopData.texturePackPath);
        }
        setListeningMode(false);
      }

      setBundleMessage('Creating bundle...');

      // Use FormData to support image upload
      const formData = new FormData();
      formData.append('name', bundleName.trim());
      formData.append('description', bundleDescription.trim());
      formData.append('buildName', buildId || bundleName.trim().toLowerCase().replace(/\s+/g, '-'));
      formData.append('vanillaIsoPath', vanillaIsoPath);
      formData.append('exportedIsoPath', exportedIsoPath);
      if (finalTexturePackPath) {
        formData.append('texturePackPath', finalTexturePackPath);
      }
      if (bundleImage) {
        formData.append('image', bundleImage);
      }

      const response = await fetch(`${API_URL}/bundle/export`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.success) {
        setBundleExportId(data.export_id);
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
      const response = await fetch(`${API_URL}/xdelta/create`, {
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
    link.href = `${API_URL}/xdelta/download-patch/${patchResult.patch_id}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Export ISO</h2>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          {!exporting && !complete && !error && (
            <>
              {/* Export Mode Cards */}
              <div className="export-mode-cards">
                {/* Quick Export Card */}
                <div className="export-mode-card">
                  <div className="card-header">
                    <h3>Quick Export</h3>
                  </div>
                  <div className="card-body">
                    <p className="card-description">
                      Auto-optimized for {costumeCount} added costume{costumeCount !== 1 ? 's' : ''}
                    </p>
                    <div className="compression-badge">
                      Compression: {recommendedCompression}x
                    </div>
                    <p className="card-note">
                      Required for console/Wii
                    </p>
                  </div>
                  <button
                    className="btn-card-export"
                    onClick={handleQuickExport}
                  >
                    Export
                  </button>
                </div>

                {/* Texture Pack Card */}
                <div className={`export-mode-card texture-pack-card ${!slippiDolphinPath ? 'disabled' : ''}`}>
                  <div className="card-header">
                    <h3>Texture Pack</h3>
                    <span className="recommended-badge">Recommended</span>
                  </div>
                  <div className="card-body">
                    <p className="card-description">
                      Best quality, no compression
                    </p>
                    <ol className="workflow-steps">
                      <li>Export ISO</li>
                      <li>Scroll through CSS in Dolphin</li>
                      <li>Done - textures auto-apply</li>
                    </ol>
                    {!slippiDolphinPath && (
                      <p className="card-warning">
                        Set Slippi path in Settings first
                      </p>
                    )}
                  </div>
                  <button
                    className="btn-card-export btn-texture-pack"
                    onClick={handleTexturePackExport}
                    disabled={!slippiDolphinPath}
                  >
                    Export
                  </button>
                </div>
              </div>

              {/* Advanced Options (Collapsible) */}
              <div className="advanced-section">
                <button
                  className="advanced-toggle"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                >
                  <span className="toggle-arrow">{showAdvanced ? '▼' : '▶'}</span>
                  Advanced Options
                </button>

                {showAdvanced && (
                  <div className="advanced-content">
                    <div className="form-group">
                      <label htmlFor="compression">
                        Manual CSP Compression
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
                        Saves memory but adds artifacts
                      </p>
                    </div>

                    <button
                      className="btn-export btn-advanced-export"
                      onClick={handleAdvancedExport}
                    >
                      Export with Custom Settings
                    </button>
                  </div>
                )}
              </div>
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

          {complete && !creatingPatch && !patchComplete && !patchError && !listeningMode && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Export Complete!</h3>
              <p>Your modified ISO is ready to download.</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download {filename}
                </button>
                <button className="btn-secondary" onClick={handleClose}>
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
                <button className="btn-secondary" onClick={handleClose}>
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
                <button className="btn-secondary" onClick={handleClose}>
                  Close
                </button>
              </div>
            </div>
          )}

          {listeningMode && (
            <div className="listening-mode">
              <div className="listening-header">
                <div className="pulse-icon"></div>
                <h3>Texture Pack Mode</h3>
              </div>

              <div className="texture-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${textureProgress.percentage}%` }}
                  ></div>
                </div>
                <span className="progress-text">
                  {textureProgress.matched} / {textureProgress.total} textures matched
                </span>
              </div>

              {/* Current Character Focus */}
              {characters.length > 0 && currentCharIndex < characters.length && (
                <div className="current-character-section">
                  <div className="current-char-header">
                    <span className="current-label">
                      {characters[currentCharIndex]?.matched === characters[currentCharIndex]?.total
                        ? 'Complete!'
                        : 'Scan next:'}
                    </span>
                    <span className="current-char-name">{characters[currentCharIndex]?.name}</span>
                  </div>
                  <div className="costume-dots">
                    {characters[currentCharIndex]?.costumes.map((costume, i) => (
                      <div
                        key={i}
                        className={`costume-dot ${costume.matched ? 'matched' : ''}`}
                        title={`Costume ${costume.index + 1}`}
                      />
                    ))}
                  </div>
                  <p className="current-char-progress">
                    {characters[currentCharIndex]?.matched} / {characters[currentCharIndex]?.total} costumes
                    {characters[currentCharIndex]?.matched === characters[currentCharIndex]?.total && ' ✓'}
                  </p>
                </div>
              )}

              {/* Character List */}
              <div className="character-list">
                <div className="char-list-header">All Characters</div>
                <div className="char-list-scroll">
                  {characters.map((char, idx) => (
                    <div
                      key={char.name}
                      className={`char-list-item ${idx === currentCharIndex ? 'current' : ''} ${char.matched === char.total ? 'complete' : ''} ${char.matched > 0 && char.matched < char.total ? 'partial' : ''}`}
                      onClick={() => setCurrentCharIndex(idx)}
                    >
                      <span className="char-name">{char.name}</span>
                      <span className="char-progress">
                        {char.matched}/{char.total}
                        {char.matched === char.total && ' ✓'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <p className="listening-instructions">
                Open the ISO in Dolphin and scroll through each character's costumes on the CSS.
                The view will auto-update as textures are matched.
              </p>

              <div className="listening-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download ISO
                </button>
                <button className="btn-done" onClick={handleStopListening}>
                  Done - Finish Texture Pack
                </button>
                <button
                  className="btn-export-bundle"
                  onClick={handleShowBundleForm}
                  style={{ background: 'var(--gradient-gold)' }}
                >
                  Export as Bundle
                </button>
              </div>
            </div>
          )}

          {/* Bundle export form */}
          {showBundleForm && (
            <div className="bundle-form">
              <h3>Export as Bundle</h3>
              <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
                Create a shareable .ssbm file that friends can install with one click!
              </p>

              <div className="form-field">
                <label>Bundle Name</label>
                <input
                  type="text"
                  value={bundleName}
                  onChange={(e) => setBundleName(e.target.value)}
                  placeholder="My Awesome Mod Pack"
                />
              </div>

              <div className="form-field">
                <label>Description (optional)</label>
                <textarea
                  value={bundleDescription}
                  onChange={(e) => setBundleDescription(e.target.value)}
                  placeholder="Describe what's in this bundle..."
                  rows={2}
                />
              </div>

              <div className="form-field">
                <label>Cover Image (optional)</label>
                <div className="image-input-row">
                  {bundleImagePreview ? (
                    <div className="image-preview">
                      <img src={bundleImagePreview} alt="Bundle preview" />
                      <button
                        className="remove-image"
                        onClick={() => {
                          setBundleImage(null);
                          setBundleImagePreview(null);
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <label className="image-select-btn">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleBundleImageChange}
                        style={{ display: 'none' }}
                      />
                      Select Image
                    </label>
                  )}
                </div>
              </div>

              <div className="form-actions">
                <button
                  className="btn-export"
                  onClick={handleStartBundleExport}
                  disabled={!bundleName.trim()}
                  style={{ background: 'var(--gradient-gold)' }}
                >
                  Create Bundle
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setShowBundleForm(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Bundle export in progress */}
          {bundleExporting && (
            <div className="export-progress">
              <div className="progress-header">
                <h3>Creating Bundle...</h3>
                <span className="progress-percentage">{bundleProgress}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${bundleProgress}%` }}
                ></div>
              </div>

              <p className="progress-message">{bundleMessage}</p>

              <div className="export-spinner">
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {/* Bundle export complete */}
          {bundleComplete && bundleResult && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Bundle Created!</h3>
              <p style={{ marginBottom: '0.5rem' }}>{bundleResult.filename}</p>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9em' }}>
                Size: {bundleResult.size_mb} MB
                {bundleResult.texture_count > 0 && ` • ${bundleResult.texture_count} textures`}
              </p>
              <p style={{
                color: 'var(--color-text-muted)',
                fontSize: '0.85rem',
                marginTop: '1rem',
                padding: '0.75rem',
                background: 'var(--color-bg-surface)',
                borderRadius: 'var(--radius-md)'
              }}>
                Share this file with friends - they can install it with one click!
              </p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownloadBundle} style={{ background: 'var(--gradient-gold)' }}>
                  Download Bundle
                </button>
                <button className="btn-secondary" onClick={handleClose}>
                  Done
                </button>
              </div>
            </div>
          )}

          {/* Bundle export error */}
          {bundleError && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Bundle Export Failed</h3>
              <p className="error-message">{bundleError}</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download ISO Anyway
                </button>
                <button className="btn-secondary" onClick={handleClose}>
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
              <button className="btn-secondary" onClick={handleClose}>
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
