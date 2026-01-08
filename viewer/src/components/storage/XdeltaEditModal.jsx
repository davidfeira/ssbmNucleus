/**
 * XdeltaEditModal - Modal for editing XDelta patch details
 */
export default function XdeltaEditModal({
  show,
  patch,
  onPatchChange,
  onSave,
  onCancel,
  onDelete,
  onUpdateImage,
  BACKEND_URL
}) {
  if (!show || !patch) return null

  const handleOverlayClick = () => {
    onCancel()
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-content" onClick={handleContentClick}>
        <h2>Edit Patch</h2>

        <div className="edit-preview">
          {patch.imageUrl ? (
            <img
              src={`${BACKEND_URL}${patch.imageUrl}?t=${Date.now()}`}
              alt={patch.name}
            />
          ) : (
            <div className="edit-placeholder">
              <span>{patch.name[0]}</span>
            </div>
          )}
          <input
            type="file"
            accept="image/*"
            onChange={onUpdateImage}
            style={{ display: 'none' }}
            id="xdelta-image-input"
          />
          <button
            className="btn-edit-screenshot"
            onClick={() => document.getElementById('xdelta-image-input').click()}
            title="Replace image"
          >
            ✎
          </button>
        </div>

        <div className="edit-field">
          <label>Name:</label>
          <input
            type="text"
            value={patch.name}
            onChange={(e) => onPatchChange({ ...patch, name: e.target.value })}
          />
        </div>

        <div className="edit-field">
          <label>Description:</label>
          <textarea
            value={patch.description || ''}
            onChange={(e) => onPatchChange({ ...patch, description: e.target.value })}
            rows={3}
          />
        </div>

        <div className="edit-buttons">
          <button className="btn-save" onClick={onSave}>
            Save
          </button>
          <button
            className="btn-cancel"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className="btn-delete-modal"
            onClick={() => {
              onDelete(patch.id)
              onCancel()
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
