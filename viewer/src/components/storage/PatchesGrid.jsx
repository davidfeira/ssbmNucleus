/**
 * PatchesGrid - XDelta patches and Bundles list display
 *
 * Features:
 * - List of patches with image, name, description, size
 * - List of bundles with image, name, description, size, texture count
 * - Edit, Download, Build ISO actions per patch
 * - Edit, Download, Install actions per bundle
 * - "Create New Patch" card to trigger creation modal
 */

import { playSound, playHoverSound } from '../../utils/sounds'
import { BACKEND_URL } from '../../config'

export default function PatchesGrid({
  xdeltaPatches,
  bundles = [],
  onEditPatch,
  onBuildIso,
  onShowCreateModal,
  onEditBundle,
  onInstallBundle
}) {
  return (
    <div className="patches-section">
      {/* Bundles Section */}
      {bundles.length > 0 && (
        <>
          <h3 style={{ margin: '0 0 1rem', color: 'var(--color-text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Bundles
          </h3>
          <div className="patches-list" style={{ marginBottom: '2rem' }}>
            {bundles.map((bundle) => (
              <div key={bundle.id} className="patch-row bundle-row">
                <div className="patch-row-image">
                  {bundle.imageUrl ? (
                    <img
                      src={`${BACKEND_URL}${bundle.imageUrl}`}
                      alt={bundle.name}
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                  ) : null}
                  <div className="patch-row-placeholder" style={{ display: bundle.imageUrl ? 'none' : 'flex', background: 'linear-gradient(135deg, #d4a574 0%, #c9956c 100%)' }}>
                    {bundle.name[0]}
                  </div>
                  <button
                    className="btn-edit-overlay"
                    onMouseEnter={playHoverSound}
                    onClick={(e) => { e.stopPropagation(); playSound('boop'); onEditBundle(bundle); }}
                    title="Edit"
                  >
                    ✎
                  </button>
                </div>

                <div className="patch-row-info">
                  <h4 className="patch-row-name">{bundle.name}</h4>
                  {bundle.description && (
                    <p className="patch-row-description">{bundle.description}</p>
                  )}
                  <p className="patch-row-size" style={{ fontSize: '0.8em', color: 'var(--color-text-muted)', margin: 0 }}>
                    {bundle.size_mb || (bundle.size / (1024 * 1024)).toFixed(2)} MB
                    {bundle.texture_count > 0 && ` • ${bundle.texture_count} textures`}
                  </p>
                </div>

                <div className="patch-row-actions">
                  <button
                    className="btn-build-iso"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); onInstallBundle(bundle); }}
                  >
                    Install
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Patches Section */}
      <h3 style={{ margin: '0 0 1rem', color: 'var(--color-text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Patches
      </h3>
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
              <button
                className="btn-edit-overlay"
                onMouseEnter={playHoverSound}
                onClick={(e) => { e.stopPropagation(); playSound('boop'); onEditPatch(patch); }}
                title="Edit"
              >
                ✎
              </button>
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
                className="btn-build-iso"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); onBuildIso(patch); }}
              >
                Build ISO
              </button>
            </div>
          </div>
        ))}

        {/* Create New Patch Card */}
        <div
          className="patch-row create-patch-row"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onShowCreateModal(); }}
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
              onMouseEnter={playHoverSound}
              onClick={(e) => {
                e.stopPropagation()
                playSound('boop')
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
