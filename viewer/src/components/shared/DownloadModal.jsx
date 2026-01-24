import { DOWNLOAD_PHASES } from '../../hooks/useDownloadQueue'
import { playSound } from '../../utils/sounds'
import './DownloadModal.css'

/**
 * Modal component for showing nucleus:// download progress
 *
 * @param {Object} props
 * @param {Object} props.download - Current download info (url, name, title)
 * @param {string} props.phase - Current phase from DOWNLOAD_PHASES
 * @param {string} props.error - Error message if phase is ERROR
 * @param {Object} props.result - Result object if phase is COMPLETE
 * @param {Function} props.onClose - Callback when modal is dismissed
 * @param {Function} props.onSlippiChoice - Callback for slippi safety choice
 */
export default function DownloadModal({
  download,
  phase,
  error,
  result,
  onClose,
  onSlippiChoice
}) {
  // Don't render if idle
  if (phase === DOWNLOAD_PHASES.IDLE || !download) {
    return null
  }

  const isProcessing = phase === DOWNLOAD_PHASES.DOWNLOADING || phase === DOWNLOAD_PHASES.IMPORTING
  const canClose = phase === DOWNLOAD_PHASES.COMPLETE || phase === DOWNLOAD_PHASES.ERROR
  const needsSlippiChoice = result?.needsSlippiChoice

  const handleOverlayClick = () => {
    if (canClose && !needsSlippiChoice) {
      playSound('back')
      onClose()
    }
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  const handleClose = () => {
    playSound('back')
    onClose()
  }

  const handleSlippiChoice = (choice) => {
    if (choice === 'cancel') {
      playSound('back')
      onClose()
    } else {
      onSlippiChoice(choice)
    }
  }

  const getStatusText = () => {
    switch (phase) {
      case DOWNLOAD_PHASES.DOWNLOADING:
        return 'Downloading...'
      case DOWNLOAD_PHASES.IMPORTING:
        return 'Importing...'
      case DOWNLOAD_PHASES.COMPLETE:
        return needsSlippiChoice ? 'Slippi Safety Warning' : 'Complete!'
      case DOWNLOAD_PHASES.ERROR:
        return 'Error'
      default:
        return ''
    }
  }

  const displayName = download.title || download.name || 'Mod'

  return (
    <div className="download-modal-overlay" onClick={handleOverlayClick}>
      <div className="download-modal-content" onClick={handleContentClick}>
        {/* Header */}
        <div className="download-modal-header">
          <h3>{needsSlippiChoice ? 'Slippi Safety Warning' : 'Importing Mod'}</h3>
        </div>

        {/* Mod name */}
        <div className="download-modal-name">{displayName}</div>

        {/* Status area */}
        <div className={`download-modal-status ${phase}`}>
          {isProcessing && (
            <div className="download-spinner" />
          )}

          {phase === DOWNLOAD_PHASES.COMPLETE && !needsSlippiChoice && (
            <div className="download-success-icon">&#x2713;</div>
          )}

          {phase === DOWNLOAD_PHASES.ERROR && (
            <div className="download-error-icon">!</div>
          )}

          <span className="download-status-text">{getStatusText()}</span>
        </div>

        {/* Error message */}
        {phase === DOWNLOAD_PHASES.ERROR && error && (
          <div className="download-error-message">{error}</div>
        )}

        {/* Slippi warning content */}
        {needsSlippiChoice && result?.unsafe_costumes && (
          <div className="download-slippi-warning">
            <p>This costume is not Slippi safe. Choose an action:</p>
            <div className="download-slippi-affected">
              <strong>Affected costumes:</strong>
              <ul>
                {result.unsafe_costumes.map((costume, idx) => (
                  <li key={idx}>{costume.character} - {costume.color}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="download-modal-actions">
          {needsSlippiChoice ? (
            <>
              <button
                className="download-btn download-btn-primary"
                onClick={() => handleSlippiChoice('fix')}
              >
                Fix & Import
              </button>
              <button
                className="download-btn download-btn-secondary"
                onClick={() => handleSlippiChoice('import_as_is')}
              >
                Import As-Is
              </button>
              <button
                className="download-btn download-btn-cancel"
                onClick={() => handleSlippiChoice('cancel')}
              >
                Cancel
              </button>
            </>
          ) : canClose ? (
            <button
              className="download-btn download-btn-close"
              onClick={handleClose}
            >
              Close
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
