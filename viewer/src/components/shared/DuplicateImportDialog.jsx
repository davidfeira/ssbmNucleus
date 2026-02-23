import { playSound } from '../../utils/sounds'

const BACKEND_URL = 'http://127.0.0.1:5000'

/**
 * Dialog shown when an imported skin already exists in the library.
 *
 * @param {boolean} show - Whether to show the dialog
 * @param {Object} data - Response data with duplicate_skins array
 * @param {Function} onChoice - Callback for user choice ('import_anyway' or 'skip')
 */
export default function DuplicateImportDialog({ show, data, onChoice }) {
  if (!show || !data) return null

  const handleOverlayClick = () => {
    playSound('back')
    onChoice('skip')
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-content" onClick={handleContentClick} style={{ maxWidth: '500px' }}>
        <h2>
          {data.mod_type === 'stage' ? 'Duplicate Stage'
            : data.mod_type === 'patch' ? 'Duplicate Patch'
            : data.mod_type === 'effect' ? 'Duplicate Effect'
            : 'Duplicate Skin'}
        </h2>

        <div style={{ padding: '1rem 0' }}>
          <p style={{ marginBottom: '1rem' }}>
            {data.mod_type === 'stage' ? 'You already have this stage.'
              : data.mod_type === 'patch' ? 'You already have this patch.'
              : data.mod_type === 'effect' ? 'You already have this effect.'
              : 'You already own this skin.'} What would you like to do?
          </p>

          {data.duplicate_skins && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
              {data.duplicate_skins.map((dup, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    background: '#2a2a2a',
                    border: '1px solid #444',
                    borderRadius: '4px',
                    padding: '0.75rem'
                  }}
                >
                  <img
                    src={`${BACKEND_URL}${dup.existing_skin.csp_url}`}
                    alt={dup.existing_skin.name}
                    style={{ width: '60px', height: '60px', objectFit: 'contain', borderRadius: '4px' }}
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                  <span>{dup.existing_skin.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <button
            className="btn-save"
            onClick={() => onChoice('import_anyway')}
            style={{ width: '100%' }}
          >
            Add Anyway
          </button>
          <button
            className="btn-cancel"
            onClick={() => { playSound('back'); onChoice('skip') }}
            style={{ width: '100%' }}
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  )
}
