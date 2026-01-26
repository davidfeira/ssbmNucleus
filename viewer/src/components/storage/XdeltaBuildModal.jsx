/**
 * XdeltaBuildModal - Build ISO from XDelta patch
 *
 * Features:
 * - Progress tracking for build process
 * - Success state with download button
 * - Error handling
 */

import { playSound, playHoverSound } from '../../utils/sounds'

export default function XdeltaBuildModal({
  show,
  xdeltaBuildState,
  xdeltaBuildPatch,
  xdeltaBuildProgress,
  xdeltaBuildMessage,
  xdeltaBuildFilename,
  xdeltaBuildError,
  onClose,
  onDownload
}) {
  if (!show) return null

  return (
    <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Build ISO</h2>
          {xdeltaBuildState !== 'building' && (
            <button className="close-btn" onMouseEnter={playHoverSound} onClick={() => { playSound('back'); onClose(); }}>×</button>
          )}
        </div>

        <div className="modal-body">
          {xdeltaBuildState === 'building' && (
            <div className="export-progress">
              <div className="progress-header">
                <h3>Building ISO...</h3>
                <span className="progress-percentage">{xdeltaBuildProgress}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${xdeltaBuildProgress}%` }}
                ></div>
              </div>

              <p className="progress-message">
                {xdeltaBuildMessage || `Applying patch: ${xdeltaBuildPatch?.name}`}
              </p>

              <div className="export-spinner">
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {xdeltaBuildState === 'complete' && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Build Complete!</h3>
              <p>Your patched ISO is ready to download.</p>
              <div className="complete-actions">
                <button className="btn-download" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); onDownload(); }}>
                  Download {xdeltaBuildFilename}
                </button>
                <button className="btn-secondary" onMouseEnter={playHoverSound} onClick={() => { playSound('back'); onClose(); }}>
                  Close
                </button>
              </div>
            </div>
          )}

          {xdeltaBuildState === 'error' && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Build Failed</h3>
              <p className="error-message">{xdeltaBuildError}</p>
              <button className="btn-secondary" onMouseEnter={playHoverSound} onClick={() => { playSound('back'); onClose(); }}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
