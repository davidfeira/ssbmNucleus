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
  onScreenshotChange,
  onSlippiRetest,
  onSlippiOverride,
  onOpenCspManager,
  onStartSkinCreator,
  onView3D,

  API_URL
}) {
  if (!show || !editingItem) return null

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

  const handleOverlayClick = () => {
    onCancel()
  }

  const handleContentClick = (e) => {
    e.stopPropagation()
  }

  return (
    <div className="edit-modal-fullscreen-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal-fullscreen" onClick={handleContentClick}>
        {/* Close Button */}
        <button
          className="edit-modal-close"
          onClick={onCancel}
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
                <div className="edit-modal-csp-container">
                  {cspPreview ? (
                    <img
                      src={cspPreview}
                      alt="New CSP preview"
                      className="edit-modal-csp-image"
                    />
                  ) : (editingItem.data.has_csp || editingItem.data.active_csp_id) ? (
                    <img
                      src={`${displayCspUrl}?t=${lastImageUpdate}`}
                      alt="CSP"
                      className="edit-modal-csp-image"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <div className="edit-modal-csp-placeholder">
                      <span>{editingItem.data.color[0]}</span>
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
                <div className="edit-modal-csp-label">Character Select Portrait</div>
              </div>

              {/* MIDDLE: Stock Icon + 3D Viewer */}
              <div className="edit-modal-stock-section">
                <div className="edit-modal-stock-container">
                  {stockPreview ? (
                    <img
                      src={stockPreview}
                      alt="New stock preview"
                      className="edit-modal-stock-image"
                    />
                  ) : editingItem.data.has_stock ? (
                    <img
                      src={`${editingItem.data.stockUrl}?t=${lastImageUpdate}`}
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
                </div>
                <div className="edit-modal-stock-label">Stock Icon</div>

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
                <div className="edit-modal-csp-container">
                  {screenshotPreview ? (
                    <img
                      src={screenshotPreview}
                      alt="New screenshot preview"
                      className="edit-modal-csp-image"
                    />
                  ) : editingItem.data.hasScreenshot ? (
                    <img
                      src={editingItem.data.screenshotUrl}
                      alt="Preview"
                      className="edit-modal-csp-image"
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
            onClick={onCancel}
            disabled={saving || deleting || exporting}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
