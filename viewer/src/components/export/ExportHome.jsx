import React from 'react';

/**
 * Minimalist export home — three one-shot actions:
 *   Export ISO    : build a ready-to-play ISO. (Advanced compression options
 *                   live in this card, since they only shape the ISO build.)
 *   Export Patch  : build the ISO, then make a small .xdelta patch (one click).
 *   Add Bundle    : build a texture-pack ISO, auto-apply HD portraits, make the
 *                   patch, and save a .ssbm into the Patches library.
 *
 * The name box edits a base name only; the ".iso" extension is shown as a fixed
 * suffix and appended at save time (and stripped if the user types it).
 */
const ExportOption = ({ accent, title, desc, button, onClick, disabled, reason }) => (
  <div className={`export-option accent-${accent} ${disabled ? 'disabled' : ''}`}>
    <div className="option-text">
      <h3>{title}</h3>
      <p>{desc}</p>
      {disabled && reason && <p className="option-reason">{reason}</p>}
    </div>
    <button className="btn-option" onClick={onClick} disabled={disabled}>
      {button}
    </button>
  </div>
);

const ExportHome = ({
  name,
  setName,
  recommendedCompression,
  slippiPath,
  vanillaPath,
  cspCompression,
  setCspCompression,
  useColorSmash,
  setUseColorSmash,
  showAdvanced,
  setShowAdvanced,
  onExportIso,
  onExportPatch,
  onAddBundle,
}) => {
  const hasVanilla = !!vanillaPath;
  const hasSlippi = !!slippiPath;

  const bundleReason = !hasVanilla && !hasSlippi
    ? 'Set your vanilla ISO and Slippi paths in Settings'
    : !hasVanilla
    ? 'Set your vanilla ISO path in Settings'
    : !hasSlippi
    ? 'Set your Slippi / Dolphin path in Settings'
    : null;

  return (
    <div className="export-home">
      <div className="form-group filename-group">
        <label htmlFor="export-name">Output name</label>
        <div className="name-input-wrap">
          <input
            id="export-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value.replace(/\.iso$/i, ''))}
            spellCheck={false}
          />
          <span className="name-suffix">.iso</span>
        </div>
      </div>

      <div className="export-options">
        {/* Export ISO — with its Advanced options attached directly below */}
        <div className="export-option accent-cyan iso-card">
          <div className="export-option-main">
            <div className="option-text">
              <h3>Export ISO</h3>
              <p>A ready-to-play ISO, auto-compressed to fit console / Wii.</p>
            </div>
            <button className="btn-option" onClick={onExportIso}>Export</button>
          </div>

          <div className="iso-advanced">
            <button className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
              <span className="toggle-arrow">{showAdvanced ? '▼' : '▶'}</span>
              Advanced
            </button>

            {showAdvanced && (
              <div className="advanced-content">
                <div className="form-group">
                  <label htmlFor="compression">
                    CSP Compression
                    {recommendedCompression < 1 && (
                      <span className="hint-recommended"> · {recommendedCompression}x recommended</span>
                    )}
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

                <p className="advanced-note">
                  Also shapes the ISO inside an Export Patch. Bundles always ship full-res textures.
                </p>
              </div>
            )}
          </div>
        </div>

        <ExportOption
          accent="teal"
          title="Export Patch"
          desc="Create an .xdelta patch to share."
          button="Export"
          onClick={onExportPatch}
          disabled={!hasVanilla}
          reason={!hasVanilla ? 'Set your vanilla ISO path in Settings' : null}
        />
        <ExportOption
          accent="gold"
          title="Add Bundle"
          desc="HD texture pack + patch, saved to your Patches library."
          button="Add"
          onClick={onAddBundle}
          disabled={!hasVanilla || !hasSlippi}
          reason={bundleReason}
        />
      </div>
    </div>
  );
};

export default ExportHome;
