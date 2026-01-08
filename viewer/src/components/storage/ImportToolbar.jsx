/**
 * ImportToolbar - Import button and message display
 *
 * Features:
 * - Different import buttons for Characters/Stages (file input) vs Patches (modal trigger)
 * - Import status message display
 * - Disabled state during import
 */
export default function ImportToolbar({
  mode,
  importing,
  importMessage,
  onFileImport,
  onShowXdeltaImportModal
}) {
  return (
    <div className="import-file-container">
      {(mode === 'characters' || mode === 'stages') ? (
        <label className="intake-import-btn" style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}>
          {importing ? 'Importing...' : 'Import File'}
          <input
            type="file"
            accept=".zip,.7z"
            onChange={onFileImport}
            disabled={importing}
            style={{ display: 'none' }}
          />
        </label>
      ) : (
        <button
          className="intake-import-btn"
          onClick={onShowXdeltaImportModal}
        >
          Import Patch
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
