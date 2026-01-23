import { playSound } from '../../utils/sounds'
import './SlippiSafetyDialog.css'

/**
 * Shared dialog component for Slippi safety warnings
 *
 * @param {boolean} show - Whether to show the dialog
 * @param {Object} data - Dialog data with unsafe_costumes array
 * @param {Function} onChoice - Callback for user choice ('fix', 'import_as_is', or 'cancel')
 * @param {boolean} isRetest - Whether this is a retest dialog (affects button labels)
 */
export default function SlippiSafetyDialog({ show, data, onChoice, isRetest = false }) {
  if (!show || !data) return null

  const handleOverlayClick = () => {
    playSound('back')
    onChoice('cancel')
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-content" onClick={handleContentClick} style={{ maxWidth: '500px' }}>
        <h2>Slippi Safety Warning</h2>

        <div style={{ padding: '1rem 0' }}>
          <p style={{ marginBottom: '1rem' }}>
            This costume is not Slippi safe. Choose an action:
          </p>

          {data.unsafe_costumes && (
            <div className="slippi-dialog-warning-box">
              <strong>Affected costumes:</strong>
              <ul style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                {data.unsafe_costumes.map((costume, idx) => (
                  <li key={idx}>{costume.character} - {costume.color}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <button
            className="btn-save"
            onClick={() => onChoice('fix')}
            style={{ width: '100%' }}
          >
            {isRetest ? 'Fix' : 'Fix & Import'}
          </button>
          <button
            className="btn-secondary"
            onClick={() => onChoice('import_as_is')}
            style={{ width: '100%' }}
          >
            {isRetest ? 'Keep As-Is' : 'Import As-Is'}
          </button>
          <button
            className="btn-cancel"
            onClick={() => { playSound('back'); onChoice('cancel'); }}
            style={{ width: '100%' }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
