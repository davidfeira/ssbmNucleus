/**
 * CspManagerModal - Modal for managing Character Select Portraits (CSPs)
 *
 * Features:
 * - Active portrait display with HD comparison slider
 * - Alternative CSPs grid (swap/remove)
 * - HD Capture section (2x, 4x, 8x, 16x options)
 * - Save/Cancel actions
 */
export default function CspManagerModal({
  show,
  cspManagerSkin,
  pendingMainCspPreview,
  hdCspInfo,
  compareSliderPosition,
  lastImageUpdate,
  alternativeCsps,
  hdResolution,
  capturingHdCsp,
  onClose,
  onCspManagerMainChange,
  onCompareSliderStart,
  onSwapCsp,
  onRemoveAlternativeCsp,
  onAddAlternativeCsp,
  onHdResolutionChange,
  onCaptureHdCsp,
  onRegenerateAltHd,
  onResetToOriginal,
  onSave,
  API_URL
}) {
  if (!show || !cspManagerSkin) return null

  // Check if an alt CSP is currently active
  const activeCspId = cspManagerSkin.active_csp_id
  const isAltActive = !!activeCspId

  // Group alternativeCsps by pose name (HD and non-HD pairs together)
  // Each group has: { poseName, nonHd, hd, isActive }
  const groupedAlts = []
  const seenPoses = new Set()

  for (const alt of alternativeCsps) {
    const poseKey = alt.poseName || alt.id // Use ID as key for user-uploaded (no pose)

    if (seenPoses.has(poseKey)) continue
    seenPoses.add(poseKey)

    const nonHd = alternativeCsps.find(a =>
      (a.poseName === alt.poseName || (!a.poseName && a.id === alt.id)) && !a.isHd
    )
    const hd = alt.poseName
      ? alternativeCsps.find(a => a.poseName === alt.poseName && a.isHd)
      : null

    const isActive = activeCspId && (
      activeCspId === nonHd?.id ||
      activeCspId === hd?.id
    )

    groupedAlts.push({
      poseName: alt.poseName,
      nonHd,
      hd,
      isActive,
      // For display, prefer non-HD image, fall back to HD
      displayAlt: nonHd || hd,
      // Index of the non-HD alt for swap handler (or HD if no non-HD)
      swapIndex: alternativeCsps.indexOf(nonHd || hd)
    })
  }

  // Find the active group
  const activeGroup = groupedAlts.find(g => g.isActive)

  // Get the URL to display in the Active Portrait area
  const getActiveDisplayUrl = () => {
    if (pendingMainCspPreview) return pendingMainCspPreview
    if (activeGroup?.nonHd) return activeGroup.nonHd.url
    if (activeGroup?.hd) return activeGroup.hd.url
    return cspManagerSkin.cspUrl
  }

  // Get the HD URL for the active CSP
  const getActiveHdUrl = () => {
    if (isAltActive && activeGroup?.hd) {
      return activeGroup.hd.url
    }
    if (isAltActive) {
      return null // Active alt has no HD pair
    }
    // Original HD CSP
    return `${API_URL.replace('/api/mex', '')}/storage/${cspManagerSkin.character}/${cspManagerSkin.id}_csp_hd.png`
  }

  const activeDisplayUrl = getActiveDisplayUrl()
  const activeHdUrl = getActiveHdUrl()
  const hasActiveHd = isAltActive
    ? !!activeGroup?.hd
    : hdCspInfo?.exists

  return (
    <div className="csp-manager-overlay" onClick={onClose}>
      <div className="csp-manager-modal" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="csp-manager-close" onClick={onClose} title="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {/* Header */}
        <div className="csp-manager-header">
          <h2>CSP Manager</h2>
          <span className="csp-manager-skin-name">{cspManagerSkin.color}</span>
        </div>

        {/* Body - Two Column Layout */}
        <div className="csp-manager-body">
          {/* Left: Main CSP */}
          <div className="csp-manager-main">
            <div className="csp-manager-main-label">
              Active Portrait
              {isAltActive && activeGroup?.poseName && (
                <span className="csp-manager-main-pose-badge">
                  {activeGroup.poseName}
                </span>
              )}
              {hasActiveHd && (
                <span className="csp-manager-main-hd-badge">
                  HD
                </span>
              )}
            </div>
            <div className="csp-manager-main-container">
              {pendingMainCspPreview ? (
                <img src={pendingMainCspPreview} alt="New CSP" className="csp-manager-main-image" />
              ) : hasActiveHd && activeHdUrl ? (
                // Before/After Comparison Mode (for original or alt with HD pair)
                <div className="csp-manager-compare-wrapper">
                  {/* Left side: Normal CSP with clip-path */}
                  <div
                    className="csp-manager-compare-before-container"
                    style={{ clipPath: `inset(0 0 0 ${compareSliderPosition}%)` }}
                  >
                    <img
                      src={`${activeDisplayUrl}?t=${lastImageUpdate}`}
                      alt="Normal CSP"
                      className="csp-manager-main-image csp-manager-compare-before"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  </div>

                  {/* Right side: HD CSP with clip-path */}
                  <div
                    className="csp-manager-compare-after-container"
                    style={{ clipPath: `inset(0 ${100 - compareSliderPosition}% 0 0)` }}
                  >
                    <img
                      src={`${activeHdUrl}?t=${lastImageUpdate}`}
                      alt="HD CSP"
                      className="csp-manager-main-image csp-manager-compare-after"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  </div>

                  {/* Slider handle */}
                  <div
                    className="csp-manager-compare-slider"
                    style={{ left: `${compareSliderPosition}%` }}
                    onMouseDown={(e) => onCompareSliderStart(e)}
                    onTouchStart={(e) => onCompareSliderStart(e)}
                  >
                    <div className="csp-manager-compare-handle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="15 18 9 12 15 6"></polyline>
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                    </div>
                  </div>

                  {/* Labels */}
                  <div className="csp-manager-compare-label csp-manager-compare-label-left">
                    Normal
                  </div>
                  <div className="csp-manager-compare-label csp-manager-compare-label-right">
                    HD
                  </div>
                </div>
              ) : (cspManagerSkin.has_csp || activeGroup) ? (
                // Normal single-image mode
                <img
                  src={`${activeDisplayUrl}?t=${lastImageUpdate}`}
                  alt="Current CSP"
                  className="csp-manager-main-image"
                  onError={(e) => e.target.style.display = 'none'}
                />
              ) : (
                <div className="csp-manager-main-placeholder">
                  <span>{cspManagerSkin.color[0]}</span>
                </div>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={onCspManagerMainChange}
                style={{ display: 'none' }}
                id="csp-manager-main-input"
              />
              <button
                className="csp-manager-main-replace-btn"
                onClick={() => document.getElementById('csp-manager-main-input').click()}
                title="Replace main CSP"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                Replace
              </button>
            </div>
          </div>

          {/* Right: Alternatives Grid */}
          <div className="csp-manager-alternatives">
            <div className="csp-manager-alternatives-header">
              <span>Alternative CSPs</span>
              <span className="csp-manager-alternatives-count">({groupedAlts.length})</span>
              {isAltActive && onResetToOriginal && (
                <button
                  className="csp-manager-reset-btn"
                  onClick={onResetToOriginal}
                  title="Reset to original CSP"
                >
                  Reset to Original
                </button>
              )}
            </div>
            <div className="csp-manager-alternatives-grid">
              {/* Show original CSP in grid when an alt is active */}
              {isAltActive && cspManagerSkin.has_csp && (
                <div
                  className="csp-manager-alt-card csp-manager-alt-card--original"
                  onClick={onResetToOriginal}
                >
                  <img
                    src={`${cspManagerSkin.cspUrl}?t=${lastImageUpdate}`}
                    alt="Original CSP"
                    className="csp-manager-alt-image"
                  />
                  <div className="csp-manager-alt-original-badge">Original</div>
                  {hdCspInfo?.exists && (
                    <div className="csp-manager-alt-hd-badge">HD</div>
                  )}
                  <div className="csp-manager-alt-overlay">
                    <span>Click to restore</span>
                  </div>
                </div>
              )}
              {groupedAlts.map((group) => {
                // Don't show active group in grid - it's in the main display
                if (group.isActive) return null

                const displayAlt = group.displayAlt
                if (!displayAlt) return null

                return (
                  <div
                    key={group.poseName || displayAlt.id}
                    className="csp-manager-alt-card"
                    onClick={() => onSwapCsp(group.swapIndex)}
                  >
                    <img src={displayAlt.url} alt={group.poseName || 'Alternative'} className="csp-manager-alt-image" />
                    {/* Pose name label */}
                    {group.poseName && (
                      <div className="csp-manager-alt-pose-label">{group.poseName}</div>
                    )}
                    {/* HD badge - show if this group has an HD version */}
                    {group.hd && (
                      <div className="csp-manager-alt-hd-badge">HD</div>
                    )}
                    {/* HD regenerate button - show if no HD version yet */}
                    {!group.hd && group.nonHd && onRegenerateAltHd && (
                      <button
                        className="csp-manager-alt-hd-btn"
                        onClick={(e) => { e.stopPropagation(); onRegenerateAltHd(group.swapIndex); }}
                        title={group.poseName ? `Regenerate "${group.poseName}" at HD` : "Regenerate at HD (default pose)"}
                      >
                        HD
                      </button>
                    )}
                    <div className="csp-manager-alt-overlay">
                      <span>Click to set active</span>
                    </div>
                    <button
                      className="csp-manager-alt-remove"
                      onClick={(e) => { e.stopPropagation(); onRemoveAlternativeCsp(group.swapIndex); }}
                      title="Remove"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                )
              })}
              {/* Add New CSP Card */}
              <div className="csp-manager-add-card" onClick={() => document.getElementById('csp-manager-alt-input').click()}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>Add CSP</span>
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={onAddAlternativeCsp}
                style={{ display: 'none' }}
                id="csp-manager-alt-input"
              />
            </div>
          </div>
        </div>

        {/* HD Capture Section */}
        <div className="csp-manager-hd-section">
          <div className="csp-manager-hd-label">
            <span>HD Capture</span>
            {hdCspInfo?.exists && (
              <span className="csp-manager-hd-badge">
                {hdCspInfo.size || hdCspInfo.resolution}
              </span>
            )}
          </div>
          <div className="csp-manager-hd-controls">
            <div className="csp-manager-hd-options">
              {['2x', '3x', '4x'].map(res => (
                <button
                  key={res}
                  className={`csp-manager-hd-option ${hdResolution === res ? 'csp-manager-hd-option--active' : ''}`}
                  onClick={() => onHdResolutionChange(res)}
                >
                  {res}
                </button>
              ))}
            </div>
            <button
              className="csp-manager-hd-capture-btn"
              onClick={onCaptureHdCsp}
              disabled={capturingHdCsp}
              title={`Capture CSP at ${hdResolution} resolution`}
            >
              {capturingHdCsp ? (
                <>
                  <span className="csp-manager-spinner"></span>
                  Capturing...
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                  Capture HD CSP
                </>
              )}
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="csp-manager-actions">
          <button className="csp-manager-btn csp-manager-btn--cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="csp-manager-btn csp-manager-btn--save" onClick={onSave}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
