/**
 * ImportToolbar - Import button and message display
 *
 * Features:
 * - Different import buttons for Characters/Stages (file input) vs Patches (modal trigger)
 * - Import status message display
 * - Disabled state during import
 */
import { playSound, playHoverSound } from '../../utils/sounds'

export default function ImportToolbar({
  mode,
  importing,
  importMessage,
  onFileImport,
  onShowXdeltaImportModal,
  onShowIsoScanModal
}) {
  return (
    <div className="import-file-container">
      {(mode === 'characters' || mode === 'stages') ? (
        <label
          className="intake-import-btn"
          style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start'); }}
        >
          {importing ? 'Importing...' : 'Import File'}
          <input
            type="file"
            accept=".zip,.7z,.dat,.usd"
            onChange={onFileImport}
            disabled={importing}
            multiple
            style={{ display: 'none' }}
          />
        </label>
      ) : (
        <button
          className="intake-import-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('start'); onShowXdeltaImportModal(); }}
        >
          Import Patch
        </button>
      )}
      {mode === 'characters' && onShowIsoScanModal && (
        <button
          className="intake-import-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('start'); onShowIsoScanModal(); }}
          disabled={importing}
          style={{ marginLeft: '0.5rem' }}
          title="Scan one or more ISOs for new skins not already in your vault"
        >
          Scan ISO
        </button>
      )}
      {importMessage && (
        <div className={`import-message ${importMessage.includes('failed') || importMessage.includes('Error') || importMessage.includes('✗') ? 'error' : 'success'}`}>
          {importMessage}
        </div>
      )}
    </div>
  )
}
