import React from 'react';
import ProgressPanel from './ProgressPanel';
import { getProgressMessage } from '../shared/progressText';

/**
 * Auto texture-pack flow: the backend names the whole pack by pure computation
 * (no Dolphin, no CSS scrolling) and copies each HD portrait into the Slippi
 * Load folder. Shows compute/placement progress, then a result summary. If
 * anything is missing the user can fall back to the manual in-Dolphin scan.
 */
const AutoTexturePanel = ({
  progress,
  result,
  error,
  onContinue,
  onManualFallback,
  onRetry,
}) => {
  if (error) {
    return (
      <div className="export-error auto-texture-panel">
        <div className="error-icon">✕</div>
        <h3>Auto texture pack failed</h3>
        <p className="error-message">{error}</p>
        <p className="auto-hint">
          You can retry, or fall back to scanning the costumes manually in Dolphin.
        </p>
        <div className="complete-actions">
          <button className="btn-export" onClick={onRetry}>Try again</button>
          <button className="btn-secondary" onClick={onManualFallback}>
            Scan manually in Dolphin
          </button>
          <button className="btn-secondary" onClick={onContinue}>
            Skip — just the ISO
          </button>
        </div>
      </div>
    );
  }

  if (result) {
    const missing = result.missingFromTable || [];
    const failed = result.copyFailed || [];
    const incomplete = missing.length > 0 || failed.length > 0;
    return (
      <div className="export-complete auto-texture-panel">
        <div className="success-icon">✓</div>
        <h3>Texture pack applied</h3>
        <p className="auto-applied-summary">
          <strong>{result.matched} / {result.total}</strong> HD portraits placed in your
          Slippi Load folder. They’ll show next time you boot — no scrolling needed.
        </p>
        {result.computed > 0 && (
          <p className="auto-subtle">
            ({result.computed} new portrait name{result.computed !== 1 ? 's' : ''} computed and cached for next time.)
          </p>
        )}
        {incomplete && (
          <div className="auto-warning-box">
            <p>
              {missing.length > 0 && `${missing.length} costume${missing.length !== 1 ? 's' : ''} couldn’t be named automatically`}
              {missing.length > 0 && failed.length > 0 && '; '}
              {failed.length > 0 && `${failed.length} portrait${failed.length !== 1 ? 's' : ''} failed to copy`}
              . You can match the rest manually in Dolphin.
            </p>
            <button className="btn-secondary" onClick={onManualFallback}>
              Match remaining in Dolphin
            </button>
          </div>
        )}
        <div className="complete-actions">
          <button className="btn-export" onClick={onContinue}>Continue</button>
        </div>
      </div>
    );
  }

  // In progress
  return (
    <ProgressPanel
      title="Building texture pack…"
      label="Auto texture pack progress"
      progressValue={progress.percentage > 0 ? progress.percentage : null}
      metaText="No Dolphin needed"
      messageText={getProgressMessage(progress.message, 'Computing portrait names…')}
    />
  );
};

export default AutoTexturePanel;
