/**
 * EditModal - Modal for editing costumes and stage variants
 *
 * Supports both costume and stage variant editing with:
 * - Image uploads (CSP, stock icons, screenshots)
 * - Name editing
 * - Slippi safety management
 * - 3D model viewing (costumes only)
 * - Texture editing via Skin Creator (costumes only)
 */
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { getAppContentPortalTarget } from './appContentPortal'
import DolphinEmbedPanel from '../shared/DolphinEmbedPanel'
import HexagonLoader from '../shared/HexagonLoader'
import { playSound } from '../../utils/sounds'

export default function EditModal({
  show,
  editingItem,
  editName,
  onNameChange,
  saving,
  deleting,
  exporting,

  // Image state
  cspPreview,
  stockPreview,
  screenshotPreview,
  lastImageUpdate,

  // Slippi state
  editSlippiSafe,
  onSlippiSafeChange,
  slippiAdvancedOpen,
  onSlippiAdvancedToggle,

  // Handlers
  onSave,
  onCancel,
  onDelete,
  onExport,
  onCspChange,
  onStockChange,
  onGenerateStock,
  onConfirmGeneratedStock,
  onDiscardGeneratedStock,
  pendingGeneratedStock,
  generatingStock,
  onRetakeCsp,
  onConfirmGeneratedCsp,
  onDiscardGeneratedCsp,
  pendingGeneratedCsp,
  generatingCsp,
  onScreenshotChange,
  onSlippiRetest,
  onSlippiOverride,
  onOpenCspManager,
  onOpenPoseManager,
  onStartSkinCreator,
  onView3D,

  // In-game test (costumes only)
  onTestInGame,
  onCaptureScreenshot,
  onReplaceWithCapture,
  testingInGame,
  testStatus,
  testResult,
  testError,
  testMode,
  onResetTest,

  // Animelee convert (costumes only) — makes a NEW copy, original untouched
  onConverted,

  API_URL
}) {
  // Aspect ratio of the loaded hero image, so the grid panel hugs it
  const [panelAspect, setPanelAspect] = useState(null)

  // Animelee convert: add/remove the inverted-hull outline as a new costume copy
  const [animeleeBusy, setAnimeleeBusy] = useState(null)   // 'add' | 'remove' | null
  const [animeleeError, setAnimeleeError] = useState(null)

  const convertAnimelee = async (mode) => {
    const d = editingItem?.data
    if (!d?.character || !d?.id || animeleeBusy) return
    setAnimeleeBusy(mode)
    setAnimeleeError(null)
    try {
      const res = await fetch(`${API_URL}/storage/animelee/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character: d.character, skinId: d.id, mode }),
      })
      const j = await res.json()
      if (j.success) {
        playSound('newSkin')
        onConverted?.(j.skin)
      } else {
        setAnimeleeError(j.error || 'Conversion failed')
      }
    } catch (e) {
      setAnimeleeError(String(e))
    } finally {
      setAnimeleeBusy(null)
    }
  }

  useEffect(() => {
    setPanelAspect(null)
  }, [editingItem?.type, editingItem?.data?.id])

  if (!show || !editingItem) return null

  const handleHeroImageLoad = (e) => {
    const { naturalWidth, naturalHeight } = e.target
    if (naturalWidth && naturalHeight) {
      setPanelAspect(naturalWidth / naturalHeight)
    }
  }

  // Get the CSP URL to display - prefer active alt CSP with HD
  const getDisplayCspUrl = () => {
    if (editingItem.type !== 'costume') return null
    const data = editingItem.data
    const baseUrl = API_URL.replace('/api/mex', '')

    // If there's an active alt CSP, use it
    if (data.active_csp_id && data.alternateCsps) {
      // First try to find HD version of the active alt
      const activeAltHd = data.alternateCsps.find(
        alt => alt.poseName && alt.isHd &&
        data.alternateCsps.some(other => other.id === data.active_csp_id && other.poseName === alt.poseName)
      )
      if (activeAltHd) {
        return `${baseUrl}${activeAltHd.url}`
      }

      // Fall back to the active alt (non-HD)
      const activeAlt = data.alternateCsps.find(alt => alt.id === data.active_csp_id)
      if (activeAlt) {
        return `${baseUrl}${activeAlt.url}`
      }
    }

    // No active alt - use original CSP, prefer HD
    if (data.has_hd_csp) {
      return data.hdCspUrl || data.cspUrl.replace('_csp.png', '_csp_hd.png')
    }
    return data.cspUrl
  }

  const displayCspUrl = getDisplayCspUrl()

  // Root-relative URLs (/storage/..., /api/mex/...) resolve via the vite proxy in
  // dev, but in the packaged app the page origin is file:// so they fail to load
  // (blank stage preview / stock icon). Prefix the backend origin for any
  // leading-'/' URL; data URIs and already-absolute URLs pass through unchanged.
  const toAbsUrl = (u) =>
    (typeof u === 'string' && u.startsWith('/'))
      ? `${API_URL.replace('/api/mex', '')}${u}`
      : u

  const handleCancel = () => {
    playSound('back')
    onCancel()
  }

  const handleOverlayClick = () => {
    handleCancel()
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  const modal = (
    <div className="edit-modal-fullscreen-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-fullscreen" onClick={handleContentClick}>
        {/* Close Button */}
        <button
          className="edit-modal-close"
          onClick={handleCancel}
          title="Close"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {/* Modal Header */}
        <div className="edit-modal-header">
          <h2>Edit {editingItem.type === 'costume' ? 'Costume' : 'Stage Variant'}</h2>
        </div>

        {/* Main Content - Horizontal Layout */}
        <div className="edit-modal-body">
          {editingItem.type === 'costume' ? (
            <>
              {/* LEFT: CSP Hero Image */}
              <div className="edit-modal-csp-section">
                <div className="edit-modal-csp-stage">
                <div className="edit-modal-csp-container" style={{ '--panel-aspect': panelAspect || 0.75 }}>
                  {pendingGeneratedCsp ? (
                    <img
                      src={pendingGeneratedCsp.dataUri}
                      alt="Retaken portrait preview"
                      className="edit-modal-csp-image"
                      onLoad={handleHeroImageLoad}
                    />
                  ) : cspPreview ? (
                    <img
                      src={cspPreview}
                      alt="New CSP preview"
                      className="edit-modal-csp-image"
                      onLoad={handleHeroImageLoad}
                    />
                  ) : (editingItem.data.has_csp || editingItem.data.active_csp_id) ? (
                    <img
                      src={`${displayCspUrl}?t=${lastImageUpdate}`}
                      alt="CSP"
                      className="edit-modal-csp-image"
                      onLoad={handleHeroImageLoad}
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <div className="edit-modal-csp-placeholder">
                      <span>{editingItem.data.color[0]}</span>
                    </div>
                  )}
                  {generatingCsp && (
                    <div
                      className="edit-modal-csp-rendering-overlay"
                      style={{
                        position: 'absolute', inset: 0, zIndex: 5,
                        display: 'flex', flexDirection: 'column', gap: '0.75rem',
                        alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(8,8,16,0.78)', borderRadius: 'inherit'
                      }}
                    >
                      <HexagonLoader size={72} label="Rendering" />
                      <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.85em' }}>
                        Rendering portrait…
                      </span>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={onCspChange}
                    style={{ display: 'none' }}
                    id="csp-file-input"
                  />
                  <button
                    className="edit-modal-image-edit-btn"
                    onClick={() => onOpenCspManager(editingItem.data)}
                    title="Manage CSPs"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>Manage CSPs</span>
                  </button>
                </div>
                </div>
                <div className="edit-modal-csp-label">Character Select Portrait</div>

                {/* Retaken portrait: confirm before the active portrait is
                    replaced (the hero above already shows the fresh render) */}
                {pendingGeneratedCsp && (
                  <div className="edit-modal-stock-confirm">
                    <div className="edit-modal-csp-confirm-note">
                      New render{pendingGeneratedCsp.poseName ? ` · ${pendingGeneratedCsp.poseName} pose` : ''}
                    </div>
                    <div className="edit-modal-stock-confirm-actions">
                      <button
                        className="edit-modal-stock-confirm-btn edit-modal-stock-confirm-btn--yes"
                        onClick={onConfirmGeneratedCsp}
                        disabled={generatingCsp}
                        title="Replace the portrait with this fresh render"
                      >
                        ✓ Use it
                      </button>
                      <button
                        className="edit-modal-stock-confirm-btn"
                        onClick={onDiscardGeneratedCsp}
                        disabled={generatingCsp}
                        title="Keep the current portrait"
                      >
                        ✗ Discard
                      </button>
                    </div>
                  </div>
                )}

                {/* Stock Icon under the CSP */}
                <div className="edit-modal-stock-container edit-modal-stock-container--under-csp">
                  {pendingGeneratedStock ? (
                    <img
                      src={pendingGeneratedStock.dataUri}
                      alt="Generated stock preview"
                      className="edit-modal-stock-image"
                    />
                  ) : stockPreview ? (
                    <img
                      src={stockPreview}
                      alt="New stock preview"
                      className="edit-modal-stock-image"
                    />
                  ) : editingItem.data.has_stock ? (
                    <img
                      src={`${toAbsUrl(editingItem.data.stockUrl)}?t=${lastImageUpdate}`}
                      alt="Stock"
                      className="edit-modal-stock-image"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <div className="edit-modal-stock-placeholder">
                      <span>{editingItem.data.color[0]}</span>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={onStockChange}
                    style={{ display: 'none' }}
                    id="stock-file-input"
                  />
                  <button
                    className="edit-modal-image-edit-btn edit-modal-image-edit-btn--small"
                    onClick={() => document.getElementById('stock-file-input').click()}
                    title="Replace stock icon"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                  {onGenerateStock && !pendingGeneratedStock && (
                    <button
                      className="edit-modal-image-edit-btn edit-modal-image-edit-btn--small edit-modal-stock-generate-btn"
                      onClick={onGenerateStock}
                      disabled={generatingStock}
                      title="Generate a stock icon from this skin's colors"
                    >
                      {generatingStock ? (
                        <span className="edit-modal-stock-generate-spinner">⟳</span>
                      ) : (
                        <span>✨</span>
                      )}
                    </button>
                  )}
                </div>
                <div className="edit-modal-stock-label">Stock Icon</div>

                {/* Generated icon: compare with the current one and confirm
                    before anything is replaced */}
                {pendingGeneratedStock && (
                  <div className="edit-modal-stock-confirm">
                    <div className="edit-modal-stock-confirm-compare">
                      {editingItem.data.has_stock ? (
                        <img
                          src={`${toAbsUrl(editingItem.data.stockUrl)}?t=${lastImageUpdate}`}
                          alt="Current stock"
                          className="edit-modal-stock-confirm-thumb"
                        />
                      ) : (
                        <div className="edit-modal-stock-confirm-thumb edit-modal-stock-confirm-thumb--empty">—</div>
                      )}
                      <span className="edit-modal-stock-confirm-arrow">→</span>
                      <img
                        src={pendingGeneratedStock.dataUri}
                        alt="Generated stock"
                        className="edit-modal-stock-confirm-thumb"
                      />
                    </div>
                    <div className="edit-modal-stock-confirm-actions">
                      <button
                        className="edit-modal-stock-confirm-btn edit-modal-stock-confirm-btn--yes"
                        onClick={onConfirmGeneratedStock}
                        disabled={generatingStock}
                        title="Replace the stock icon with the generated one"
                      >
                        ✓ Use it
                      </button>
                      <button
                        className="edit-modal-stock-confirm-btn"
                        onClick={onDiscardGeneratedStock}
                        disabled={generatingStock}
                        title="Keep the current stock icon"
                      >
                        ✗ Discard
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* MIDDLE: Action Buttons */}
              <div className="edit-modal-stock-section">
                {/* Manage CSPs Button */}
                {onOpenCspManager && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={() => onOpenCspManager(editingItem.data)}
                    disabled={saving || deleting || exporting}
                    title="Swap, upload, or generate portraits for this costume"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                      <circle cx="8.5" cy="8.5" r="1.5"></circle>
                      <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                    <span>Manage CSPs</span>
                  </button>
                )}

                {/* Manage Poses Button */}
                {onOpenPoseManager && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={onOpenPoseManager}
                    disabled={saving || deleting || exporting}
                    title="Create poses and batch-generate portraits from them"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="5" r="2"></circle>
                      <path d="M12 7v5"></path>
                      <path d="M9 22l3-6 3 6"></path>
                      <path d="M7 12l5 2 5-2"></path>
                    </svg>
                    <span>Manage Poses</span>
                  </button>
                )}

                {/* Retake CSP Button — re-render the portrait with the active pose */}
                {onRetakeCsp && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={onRetakeCsp}
                    disabled={saving || deleting || exporting || testingInGame || generatingCsp}
                    title="Re-render the character-select portrait from this costume using the active pose (usually the default pose)"
                  >
                    {generatingCsp ? (
                      <span className="edit-modal-action-spinner"></span>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <polyline points="1 20 1 14 7 14"></polyline>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                      </svg>
                    )}
                    <span>{generatingCsp ? 'Rendering…' : 'Retake CSP'}</span>
                  </button>
                )}

                {/* View 3D Button */}
                <button
                  className="edit-modal-view3d-btn"
                  onClick={onView3D}
                  disabled={saving || deleting || exporting}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                  </svg>
                  <span>View 3D Model</span>
                </button>

                {/* Edit in Skin Creator Button */}
                {onStartSkinCreator && (
                  <button
                    className="edit-modal-skincreator-btn"
                    onClick={() => onStartSkinCreator(editingItem.data)}
                    disabled={saving || deleting || exporting}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>Edit Textures</span>
                  </button>
                )}

                {/* Test In Game Button */}
                {onTestInGame && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={onTestInGame}
                    disabled={saving || deleting || exporting || testingInGame}
                    title="Build a one-costume test ISO and play a short match to verify it loads"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="6" width="20" height="12" rx="6"></rect>
                      <line x1="6" y1="12" x2="10" y2="12"></line>
                      <line x1="8" y1="10" x2="8" y2="14"></line>
                      <line x1="15" y1="13" x2="15.01" y2="13"></line>
                      <line x1="18" y1="11" x2="18.01" y2="11"></line>
                    </svg>
                    <span>Test in Game</span>
                  </button>
                )}

                {/* Animelee outline — add/remove as a NEW copy (original kept).
                    Gated on onConverted so it only shows where fully wired (the
                    vanilla-character vault), not custom-character costumes. */}
                {onConverted && editingItem.data?.character && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={() => convertAnimelee('add')}
                    disabled={saving || deleting || exporting || testingInGame || !!animeleeBusy}
                    title="Make a copy of this costume with the Animelee black outline added"
                  >
                    {animeleeBusy === 'add' ? (
                      <span className="edit-modal-action-spinner"></span>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2L12 3z"></path>
                      </svg>
                    )}
                    <span>{animeleeBusy === 'add' ? 'Working…' : 'Animelee Copy'}</span>
                  </button>
                )}

                {onConverted && editingItem.data?.character && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={() => convertAnimelee('remove')}
                    disabled={saving || deleting || exporting || testingInGame || !!animeleeBusy}
                    title="Make a copy of this costume with the Animelee outline removed"
                  >
                    {animeleeBusy === 'remove' ? (
                      <span className="edit-modal-action-spinner"></span>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="9"></circle>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                      </svg>
                    )}
                    <span>{animeleeBusy === 'remove' ? 'Working…' : 'Remove Outline'}</span>
                  </button>
                )}

                {animeleeError && (
                  <div style={{ color: 'var(--color-danger, #e66)', fontSize: 12, marginTop: 6, textAlign: 'center' }}>
                    {animeleeError}
                  </div>
                )}
              </div>

              {/* RIGHT: Controls Panel */}
              <div className="edit-modal-controls-section">
                {/* Color Name */}
                <div className="edit-modal-field">
                  <label>Color Name</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => onNameChange(e.target.value)}
                    placeholder="Enter name..."
                    disabled={saving || deleting}
                    autoFocus
                  />
                </div>

                {/* Slippi Status Badge */}
                <div className="edit-modal-slippi-section">
                  <div className={`edit-modal-slippi-badge ${editingItem.data.slippi_safe ? 'edit-modal-slippi-badge--safe' : 'edit-modal-slippi-badge--unsafe'}`}>
                    <div className="edit-modal-slippi-indicator"></div>
                    <span>{editingItem.data.slippi_safe ? 'Slippi Safe' : 'Not Slippi Safe'}</span>
                    {editingItem.data.slippi_manual_override && (
                      <span className="edit-modal-slippi-override">(Override)</span>
                    )}
                  </div>

                  {/* Collapsible Advanced Controls */}
                  <button
                    className="edit-modal-slippi-toggle"
                    onClick={onSlippiAdvancedToggle}
                  >
                    <span>Advanced</span>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      style={{ transform: slippiAdvancedOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>

                  <div className={`edit-modal-slippi-advanced ${slippiAdvancedOpen ? 'edit-modal-slippi-advanced--open' : ''}`}>
                    <div className="edit-modal-slippi-advanced-inner">
                      {/* Character Info */}
                      <div className="edit-modal-info-card">
                        <div className="edit-modal-info-row">
                          <span className="edit-modal-info-label">Character</span>
                          <span className="edit-modal-info-value">{editingItem.data.character}</span>
                        </div>
                        <div className="edit-modal-info-row">
                          <span className="edit-modal-info-label">Slot ID</span>
                          <span className="edit-modal-info-value edit-modal-info-value--mono">{editingItem.data.id}</span>
                        </div>
                      </div>

                      <button
                        className="edit-modal-slippi-retest-btn"
                        onClick={() => onSlippiRetest(false)}
                        disabled={saving || deleting}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="23 4 23 10 17 10"></polyline>
                          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                        </svg>
                        Retest Safety
                      </button>

                      <div className="edit-modal-slippi-override-select">
                        <label>Manual Override</label>
                        <select
                          value={editingItem.data.slippi_safe ? 'safe' : 'unsafe'}
                          onChange={(e) => {
                            const newStatus = e.target.value === 'safe'
                            if (newStatus !== editingItem.data.slippi_safe) {
                              onSlippiOverride()
                            }
                          }}
                          disabled={saving || deleting}
                        >
                          <option value="safe">Slippi Safe</option>
                          <option value="unsafe">Not Slippi Safe</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Stage Variant Layout - Simplified 2-column */
            <>
              {/* LEFT: Stage Screenshot */}
              <div className="edit-modal-csp-section">
                <div className="edit-modal-csp-stage">
                <div className="edit-modal-csp-container" style={{ '--panel-aspect': panelAspect || (4 / 3) }}>
                  {screenshotPreview ? (
                    <img
                      src={screenshotPreview}
                      alt="New screenshot preview"
                      className="edit-modal-csp-image"
                      onLoad={handleHeroImageLoad}
                    />
                  ) : editingItem.data.hasScreenshot ? (
                    <img
                      src={`${toAbsUrl(editingItem.data.screenshotUrl)}?t=${lastImageUpdate}`}
                      alt="Preview"
                      className="edit-modal-csp-image"
                      onLoad={handleHeroImageLoad}
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <div className="edit-modal-csp-placeholder">
                      <span>{editingItem.data.name[0]}</span>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={onScreenshotChange}
                    style={{ display: 'none' }}
                    id="screenshot-file-input"
                  />
                  <button
                    className="edit-modal-image-edit-btn"
                    onClick={() => document.getElementById('screenshot-file-input').click()}
                    title="Replace screenshot"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>Edit Screenshot</span>
                  </button>
                </div>
                </div>
                <div className="edit-modal-csp-label">Stage Preview</div>
              </div>

              {/* RIGHT: Controls Panel for Stages */}
              <div className="edit-modal-controls-section edit-modal-controls-section--wide">
                {/* Variant Name */}
                <div className="edit-modal-field">
                  <label>Variant Name</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => onNameChange(e.target.value)}
                    placeholder="Enter name..."
                    disabled={saving || deleting}
                    autoFocus
                  />
                </div>

                {/* Test In Game (stage skin) */}
                {onTestInGame && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={onTestInGame}
                    disabled={saving || deleting || exporting || testingInGame}
                    title="Build a one-skin test ISO and play a short match (holds the DAS button) to verify it loads"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="6" width="20" height="12" rx="6"></rect>
                      <line x1="6" y1="12" x2="10" y2="12"></line>
                      <line x1="8" y1="10" x2="8" y2="14"></line>
                      <line x1="15" y1="13" x2="15.01" y2="13"></line>
                      <line x1="18" y1="11" x2="18.01" y2="11"></line>
                    </svg>
                    <span>Test in Game</span>
                  </button>
                )}

                {/* Capture stage screenshot (stage skin / DAS variant) */}
                {onCaptureScreenshot && (
                  <button
                    className="edit-modal-view3d-btn"
                    onClick={onCaptureScreenshot}
                    disabled={saving || deleting || exporting || testingInGame}
                    title="Boot the stage alone in a throwaway Dolphin and grab a clean whole-stage screenshot to use as the preview"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                      <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                    <span>Capture Screenshot</span>
                  </button>
                )}

                {/* Slippi Status Badge for Stages */}
                <div className="edit-modal-slippi-section">
                  <div className={`edit-modal-slippi-badge ${
                    editSlippiSafe === null ? 'edit-modal-slippi-badge--unknown' :
                    editSlippiSafe ? 'edit-modal-slippi-badge--safe' : 'edit-modal-slippi-badge--unsafe'
                  }`}>
                    <div className="edit-modal-slippi-indicator"></div>
                    <span>
                      {editSlippiSafe === null ? 'Unknown' : editSlippiSafe ? 'Slippi Safe' : 'Not Slippi Safe'}
                    </span>
                  </div>

                  {/* Collapsible Advanced Controls */}
                  <button
                    className="edit-modal-slippi-toggle"
                    onClick={onSlippiAdvancedToggle}
                  >
                    <span>Advanced</span>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      style={{ transform: slippiAdvancedOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>

                  <div className={`edit-modal-slippi-advanced ${slippiAdvancedOpen ? 'edit-modal-slippi-advanced--open' : ''}`}>
                    <div className="edit-modal-slippi-advanced-inner">
                      {/* Stage Info */}
                      <div className="edit-modal-info-card">
                        <div className="edit-modal-info-row">
                          <span className="edit-modal-info-label">Stage</span>
                          <span className="edit-modal-info-value">{editingItem.data.stageName}</span>
                        </div>
                        <div className="edit-modal-info-row">
                          <span className="edit-modal-info-label">Slot ID</span>
                          <span className="edit-modal-info-value edit-modal-info-value--mono">{editingItem.data.id}</span>
                        </div>
                      </div>

                      <p className="edit-modal-slippi-note">Stages cannot be auto-tested. Set manually.</p>
                      <div className="edit-modal-slippi-override-select">
                        <label>Safety Status</label>
                        <select
                          value={editSlippiSafe === null ? 'unknown' : (editSlippiSafe ? 'safe' : 'unsafe')}
                          onChange={(e) => {
                            const newValue = e.target.value
                            if (newValue === 'unknown') {
                              onSlippiSafeChange(null)
                            } else {
                              onSlippiSafeChange(newValue === 'safe')
                            }
                          }}
                          disabled={saving || deleting}
                        >
                          <option value="unknown">Unknown</option>
                          <option value="safe">Slippi Safe</option>
                          <option value="unsafe">Not Slippi Safe</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Bottom Action Bar */}
        <div className="edit-modal-actions">
          <button
            className="edit-modal-action-btn edit-modal-action-btn--save"
            onClick={onSave}
            disabled={saving || deleting || exporting}
          >
            {saving ? (
              <>
                <span className="edit-modal-action-spinner"></span>
                Saving...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                  <polyline points="17 21 17 13 7 13 7 21"></polyline>
                  <polyline points="7 3 7 8 15 8"></polyline>
                </svg>
                Save
              </>
            )}
          </button>
          <button
            className="edit-modal-action-btn edit-modal-action-btn--export"
            onClick={onExport}
            disabled={saving || deleting || exporting}
          >
            {exporting ? (
              <>
                <span className="edit-modal-action-spinner"></span>
                Exporting...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                Export
              </>
            )}
          </button>
          <button
            className="edit-modal-action-btn edit-modal-action-btn--delete"
            onClick={onDelete}
            disabled={saving || deleting || exporting}
          >
            {deleting ? (
              <>
                <span className="edit-modal-action-spinner"></span>
                Deleting...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Delete
              </>
            )}
          </button>
          <button
            className="edit-modal-action-btn edit-modal-action-btn--cancel"
            onClick={handleCancel}
            disabled={saving || deleting || exporting}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            Cancel
          </button>
        </div>

        {/* In-game test overlay (progress / result / error) */}
        {(testingInGame || testResult || testError) && (
          <div
            className="edit-modal-test-overlay"
            style={{
              position: 'absolute', inset: 0, zIndex: 20, borderRadius: 'inherit',
              background: 'rgba(8,8,16,0.92)', display: 'flex',
              alignItems: 'center', justifyContent: 'center'
            }}
          >
            {/* While testing: a fixed-height flex column, NEVER scrollable --
                the embedded Dolphin floats over the page and wouldn't clip, so
                the embed flex-fills whatever height the text leaves over. The
                560px scrollable wrapper is for the result/error states. */}
            <div style={testingInGame
              ? { width: '94%', height: '94%', minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', textAlign: 'center', padding: '1.5rem' }
              : { width: '90%', maxWidth: '560px', maxHeight: '92%', overflowY: 'auto', textAlign: 'center', padding: '1.5rem' }}>
              {testingInGame ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                    <HexagonLoader
                      size={88}
                      label="Testing in game"
                      progress={Number.isFinite(testStatus?.percentage) ? testStatus.percentage : null}
                      centerLabel={`${Math.round(testStatus?.percentage || 0)}%`}
                      minimumVisibleProgress={4}
                    />
                  </div>
                  <h3 style={{ color: 'var(--color-text-primary)', marginBottom: '0.5rem' }}>Testing in game…</h3>
                  <p style={{ color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                    {testStatus?.message || 'Working…'}
                  </p>
                  {/* Embedded for tests AND captures (shots grab the embedded
                      window via PrintWindow — small resolution trade for not
                      having a floating Dolphin over the app). */}
                  <DolphinEmbedPanel active fill />
                  <p style={{ fontSize: '0.8em', color: 'var(--color-text-secondary)', maxWidth: 560, margin: '1rem auto 0' }}>
                    Builds a one-costume ISO and plays a short match in a throwaway Dolphin.
                    Your Slippi setup is untouched, and it never goes online.
                  </p>
                </>
              ) : testError ? (
                <>
                  <h3 style={{ color: 'var(--color-error, #e74c3c)', marginBottom: '0.75rem' }}>Test error</h3>
                  <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>{testError}</p>
                  <button className="edit-modal-action-btn edit-modal-action-btn--cancel" onClick={onResetTest}>
                    Close
                  </button>
                </>
              ) : testResult ? (
                <>
                  <div style={{
                    display: 'inline-block', padding: '0.35rem 1.1rem', borderRadius: 'var(--radius-md)',
                    fontWeight: 700, fontSize: '1.15em', marginBottom: '0.75rem', color: '#fff',
                    background: testResult.success ? 'var(--color-success, #2ecc71)' : 'var(--color-error, #e74c3c)'
                  }}>
                    {testResult.captured ? '✓ CAPTURED' : testResult.success ? '✓ PASS' : `✕ ${String(testResult.verdict || '').toUpperCase()}`}
                  </div>
                  <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>{testResult.reason}</p>
                  {testResult.onlineAborted && (
                    <p style={{ color: 'var(--color-warning, #f39c12)', marginBottom: '1rem' }}>
                      Stopped before going online — no matchmaking occurred.
                    </p>
                  )}
                  {testResult.screenshot && (
                    <img
                      src={testResult.screenshot}
                      alt="In-game screenshot"
                      style={{ maxWidth: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', marginBottom: '1rem' }}
                    />
                  )}
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {testResult.captured ? (
                      <>
                        <button
                          className="edit-modal-action-btn edit-modal-action-btn--export"
                          onClick={() => onReplaceWithCapture && onReplaceWithCapture(testResult.screenshot)}
                        >
                          Replace Current Screenshot
                        </button>
                        <button className="edit-modal-action-btn edit-modal-action-btn--cancel" onClick={onCaptureScreenshot}>
                          Retake
                        </button>
                        <button className="edit-modal-action-btn edit-modal-action-btn--cancel" onClick={onResetTest}>
                          Discard
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="edit-modal-action-btn edit-modal-action-btn--export" onClick={onTestInGame}>
                          Test again
                        </button>
                        <button className="edit-modal-action-btn edit-modal-action-btn--cancel" onClick={onResetTest}>
                          Close
                        </button>
                      </>
                    )}
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}
