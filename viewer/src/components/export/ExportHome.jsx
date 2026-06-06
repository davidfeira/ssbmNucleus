import React from 'react';

/**
 * Minimalist export home — three one-shot actions:
 *   Export ISO    : build a ready-to-play ISO.
 *   Export Patch  : build the ISO, then make a small .xdelta patch (one click).
 *   Add Bundle    : build a texture-pack ISO, auto-apply HD portraits, make the
 *                   patch, and save a .ssbm into the Patches library.
 *
 * Compression / Color Smash live behind a low-key Advanced disclosure.
 */
// Inline line-icons (stroke = currentColor, tinted per accent) — no emoji.
const svgProps = {
  viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
  strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round',
};
const IconDisc = () => (
  <svg {...svgProps}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3" /></svg>
);
const IconDelta = () => (
  <svg {...svgProps}><path d="M12 4 L20.5 19.5 H3.5 Z" /><path d="M9 14 h6" /></svg>
);
const IconBox = () => (
  <svg {...svgProps}>
    <path d="M12 3 L20 7.5 V16.5 L12 21 L4 16.5 V7.5 Z" />
    <path d="M4 7.5 L12 12 L20 7.5" />
    <path d="M12 12 V21" />
  </svg>
);

const ExportOption = ({ icon, accent, title, desc, button, onClick, disabled, reason }) => (
  <div className={`export-option accent-${accent} ${disabled ? 'disabled' : ''}`}>
    <div className="option-icon">{icon}</div>
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
  filename,
  setFilename,
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
        <label htmlFor="export-filename">Output file name</label>
        <input
          id="export-filename"
          type="text"
          value={filename}
          onChange={(e) => setFilename(e.target.value)}
          spellCheck={false}
        />
      </div>

      <div className="export-options">
        <ExportOption
          icon={<IconDisc />}
          accent="cyan"
          title="Export ISO"
          desc="A ready-to-play ISO, auto-compressed to fit console / Wii."
          button="Export"
          onClick={onExportIso}
        />
        <ExportOption
          icon={<IconDelta />}
          accent="teal"
          title="Export Patch"
          desc="Builds the ISO and makes a small .xdelta patch to share."
          button="Export"
          onClick={onExportPatch}
          disabled={!hasVanilla}
          reason={!hasVanilla ? 'Set your vanilla ISO path in Settings' : null}
        />
        <ExportOption
          icon={<IconBox />}
          accent="gold"
          title="Add Bundle"
          desc="HD texture pack + patch, saved to your Patches library."
          button="Add"
          onClick={onAddBundle}
          disabled={!hasVanilla || !hasSlippi}
          reason={bundleReason}
        />
      </div>

      <div className="advanced-section">
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
              <p className="color-smash-info">
                Applies to Export ISO / Patch. Bundles always use full-res textures.
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
              <p className="color-smash-info">Saves memory but adds artifacts.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportHome;
