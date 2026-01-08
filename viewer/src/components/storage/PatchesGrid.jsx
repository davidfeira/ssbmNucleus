/**
 * PatchesGrid - XDelta patches list display
 *
 * Features:
 * - List of patches with image, name, description, size
 * - Edit, Download, Build ISO actions per patch
 * - "Create New Patch" card to trigger creation modal
 */

const BACKEND_URL = 'http://127.0.0.1:5000'

export default function PatchesGrid({
  xdeltaPatches,
  onEditPatch,
  onDownloadPatch,
  onBuildIso,
  onShowCreateModal
}) {
  return (
    <div className="patches-section">
      <div className="patches-list">
        {xdeltaPatches.map((patch) => (
          <div key={patch.id} className="patch-row">
            <div className="patch-row-image">
              {patch.imageUrl ? (
                <img
                  src={`${BACKEND_URL}${patch.imageUrl}`}
                  alt={patch.name}
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
              ) : null}
              <div className="patch-row-placeholder" style={{ display: patch.imageUrl ? 'none' : 'flex' }}>
                {patch.name[0]}
              </div>
            </div>

            <div className="patch-row-info">
              <h4 className="patch-row-name">{patch.name}</h4>
              {patch.description && (
                <p className="patch-row-description">{patch.description}</p>
              )}
              {patch.size && (
                <p className="patch-row-size" style={{ fontSize: '0.8em', color: 'var(--color-text-muted)', margin: 0 }}>
                  {(patch.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              )}
            </div>

            <div className="patch-row-actions">
              <button
                className="btn-edit-small"
                onClick={() => onEditPatch(patch)}
                title="Edit"
              >
                ✎
              </button>
              <button
                className="btn-edit-small"
                onClick={() => onDownloadPatch(patch.id)}
                title="Download Patch"
                style={{ fontSize: '14px' }}
              >
                ⬇
              </button>
              <button
                className="btn-build-iso"
                onClick={() => onBuildIso(patch)}
              >
                Build ISO
              </button>
            </div>
          </div>
        ))}

        {/* Create New Patch Card */}
        <div
          className="patch-row create-patch-row"
          onClick={onShowCreateModal}
          style={{ cursor: 'pointer', borderStyle: 'dashed' }}
        >
          <div className="patch-row-image">
            <div className="patch-row-placeholder" style={{ display: 'flex', fontSize: '2rem' }}>
              +
            </div>
          </div>

          <div className="patch-row-info">
            <h4 className="patch-row-name">Create New Patch</h4>
            <p className="patch-row-description">Create a patch from a modded ISO</p>
          </div>

          <div className="patch-row-actions">
            <button
              className="btn-build-iso"
              onClick={(e) => {
                e.stopPropagation()
                onShowCreateModal()
              }}
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
