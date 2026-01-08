/**
 * XdeltaImportModal - Modal for importing XDelta patches
 */
export default function XdeltaImportModal({
  show,
  importData,
  onImportDataChange,
  importing,
  onImport,
  onCancel
}) {
  if (!show) return null

  const handleOverlayClick = () => {
    onCancel()
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    onImportDataChange({
      ...importData,
      file,
      name: importData.name || (file?.name.replace('.xdelta', '') || '')
    })
  }

  const handleCancel = () => {
    onCancel()
  }

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-content" onClick={handleContentClick}>
        <h2>Import XDelta Patch</h2>

        <div className="edit-field">
          <label>XDelta File:</label>
          <input
            type="file"
            accept=".xdelta"
            onChange={handleFileChange}
          />
        </div>

        <div className="edit-field">
          <label>Name:</label>
          <input
            type="text"
            value={importData.name}
            onChange={(e) => onImportDataChange({ ...importData, name: e.target.value })}
            placeholder="Patch name..."
          />
        </div>

        <div className="edit-field">
          <label>Description (optional):</label>
          <textarea
            value={importData.description}
            onChange={(e) => onImportDataChange({ ...importData, description: e.target.value })}
            placeholder="Description..."
            rows={3}
          />
        </div>

        <div className="edit-field">
          <label>Image (optional):</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => onImportDataChange({ ...importData, image: e.target.files[0] })}
          />
        </div>

        <div className="edit-buttons">
          <button
            className="btn-save"
            onClick={onImport}
            disabled={importing || !importData.file}
          >
            {importing ? 'Importing...' : 'Import'}
          </button>
          <button
            className="btn-cancel"
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
