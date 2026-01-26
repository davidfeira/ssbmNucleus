/**
 * BundleEditModal - Modal for editing bundle details
 */
import { playSound, playHoverSound } from '../../utils/sounds'

export default function BundleEditModal({
  show,
  bundle,
  onBundleChange,
  onSave,
  onCancel,
  onDelete,
  onUpdateImage,
  onDownload,
  BACKEND_URL
}) {
  if (!show || !bundle) return null

  const handleOverlayClick = () => {
    playSound('back')
    onCancel()
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  return (
    <div className="edit-modal-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-content" onClick={handleContentClick}>
        <h2>Edit Bundle</h2>

        <div className="edit-preview">
          {bundle.imageUrl ? (
            <img
              src={`${BACKEND_URL}${bundle.imageUrl}?t=${Date.now()}`}
              alt={bundle.name}
            />
          ) : (
            <div className="edit-placeholder" style={{ background: 'linear-gradient(135deg, #d4a574 0%, #c9956c 100%)' }}>
              <span>{bundle.name[0]}</span>
            </div>
          )}
          <input
            type="file"
            accept="image/*"
            onChange={onUpdateImage}
            style={{ display: 'none' }}
            id="bundle-image-input"
          />
          <button
            className="btn-edit-screenshot"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); document.getElementById('bundle-image-input').click(); }}
            title="Replace image"
          >
            ✎
          </button>
        </div>

        <div className="edit-field">
          <label>Name:</label>
          <input
            type="text"
            value={bundle.name}
            onChange={(e) => onBundleChange({ ...bundle, name: e.target.value })}
          />
        </div>

        <div className="edit-field">
          <label>Description:</label>
          <textarea
            value={bundle.description || ''}
            onChange={(e) => onBundleChange({ ...bundle, description: e.target.value })}
            rows={3}
          />
        </div>

        <div className="edit-buttons">
          <button className="btn-save" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); onSave(); }}>
            Save
          </button>
          <button
            className="btn-export"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); onDownload(bundle.id); }}
          >
            Export
          </button>
          <button
            className="btn-cancel"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('back'); onCancel(); }}
          >
            Cancel
          </button>
          <button
            className="btn-delete-modal"
            onMouseEnter={playHoverSound}
            onClick={() => {
              if (confirm('Are you sure you want to delete this bundle?')) {
                playSound('boop')
                onDelete(bundle.id)
                onCancel()
              }
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
