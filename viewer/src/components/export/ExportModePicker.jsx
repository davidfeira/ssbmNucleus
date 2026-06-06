import React from 'react';

/**
 * The initial export screen: pick how to ship the project.
 *
 *  - Quick Export   -> one ISO, auto-compressed for console/Wii or plain sharing.
 *  - Texture Pack   -> best quality; HD portraits applied automatically (no Dolphin).
 *  - Advanced       -> manual compression / Color Smash.
 *
 * The filename is editable up top so it applies to every mode.
 */
const ExportModePicker = ({
  filename,
  setFilename,
  recommendedCompression,
  costumeCount,
  slippiPath,
  cspCompression,
  setCspCompression,
  useColorSmash,
  setUseColorSmash,
  showAdvanced,
  setShowAdvanced,
  onQuickExport,
  onTexturePackExport,
  onAdvancedExport,
}) => {
  const hasSlippi = !!slippiPath;

  return (
    <div className="export-picker">
      {/* Output filename — applies to every mode */}
      <div className="form-group filename-group">
        <label htmlFor="export-filename">Output file name</label>
        <input
          id="export-filename"
          type="text"
          value={filename}
          onChange={(e) => setFilename(e.target.value)}
          spellCheck={false}
        />
      </div>

      <div className="export-mode-cards">
        {/* Quick Export */}
        <div className="export-mode-card">
          <div className="card-header">
            <h3>Quick Export</h3>
          </div>
          <div className="card-body">
            <p className="card-description">
              One ready-to-play ISO. Auto-compressed for {costumeCount} added
              costume{costumeCount !== 1 ? 's' : ''} so it fits on console / Wii.
            </p>
            <div className="compression-badge">Compression: {recommendedCompression}x</div>
            <p className="card-note">Best for sharing a single file.</p>
          </div>
          <button className="btn-card-export" onClick={onQuickExport}>
            Export ISO
          </button>
        </div>

        {/* Texture Pack — auto by default */}
        <div className={`export-mode-card texture-pack-card ${!hasSlippi ? 'disabled' : ''}`}>
          <div className="card-header">
            <h3>Texture Pack</h3>
            <span className="recommended-badge">Recommended</span>
          </div>
          <div className="card-body">
            <p className="card-description">
              Best quality — full-res portraits load as an HD texture pack.
            </p>
            <ol className="workflow-steps">
              <li>Export the ISO</li>
              <li>Portraits named &amp; placed automatically</li>
              <li>Done — no Dolphin, no scrolling</li>
            </ol>
            {!hasSlippi && (
              <p className="card-warning">Set your Slippi/Dolphin path in Settings first.</p>
            )}
          </div>
          <button
            className="btn-card-export btn-texture-pack"
            onClick={() => onTexturePackExport('auto')}
            disabled={!hasSlippi}
          >
            Export + Texture Pack
          </button>
          {hasSlippi && (
            <button
              className="link-button texture-manual-link"
              onClick={() => onTexturePackExport('manual')}
              title="Boot the ISO and scroll the CSS in Dolphin to harvest textures the old way"
            >
              Scan manually in Dolphin instead →
            </button>
          )}
        </div>
      </div>

      {/* Advanced (compression / Color Smash) */}
      <div className="advanced-section">
        <button className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
          <span className="toggle-arrow">{showAdvanced ? '▼' : '▶'}</span>
          Advanced Options
        </button>

        {showAdvanced && (
          <div className="advanced-content">
            <div className="form-group">
              <label htmlFor="compression">Manual CSP Compression</label>
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
                    if (!isNaN(val) && val >= 0.1 && val <= 1.0) setCspCompression(val);
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
              <p className="color-smash-info">Saves memory but adds artifacts.</p>
            </div>

            <button className="btn-export btn-advanced-export" onClick={onAdvancedExport}>
              Export with Custom Settings
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportModePicker;
