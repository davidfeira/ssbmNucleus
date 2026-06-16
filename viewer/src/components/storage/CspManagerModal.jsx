/**
 * CspManagerModal - Modal for managing Character Select Portraits (CSPs)
 *
 * Features:
 * - Active portrait display with HD comparison slider
 * - Unified portraits grid (original + alternatives, click to set active)
 * - One-click HD generation (always 4x)
 * - Save/Cancel actions
 * - Upload modal for Normal/HD slot selection
 */
import { useState } from 'react'
import { createPortal } from 'react-dom'
import { getAppContentPortalTarget } from './appContentPortal'
import { playSound } from '../../utils/sounds'

// Sub-modal for uploading a CSP. One image: the app scales it down for the
// game and keeps up to a 4x copy as the HD vault preview.
function CspUploadModal({
  show,
  uploadTarget, // 'main' or 'alt'
  existingNormalUrl,
  onConfirm,
  onCancel,
  onOpenPoseManager // optional: offer "generate from pose" path when adding an alt
}) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)

  if (!show) return null

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0]
    if (!selected) return

    const reader = new FileReader()
    reader.onload = (ev) => {
      setFile(selected)
      setPreview(ev.target.result)
    }
    reader.readAsDataURL(selected)
  }

  const handleConfirm = () => {
    onConfirm({ file })
    setFile(null)
    setPreview(null)
  }

  const handleCancel = () => {
    setFile(null)
    setPreview(null)
    onCancel()
  }

  // For "add" we offer two equal paths: generate from a pose (primary) or upload
  const showPoseOption = uploadTarget === 'alt' && !!onOpenPoseManager

  const modal = (
    <div className="csp-upload-overlay" onClick={handleCancel}>
      <div className="csp-upload-modal" onClick={(e) => e.stopPropagation()}>
        <div className="csp-upload-header">
          <h3>{uploadTarget === 'main' ? 'Replace Active CSP' : 'Add CSP'}</h3>
          <button className="csp-upload-close" onClick={handleCancel}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className={`csp-upload-body ${showPoseOption ? '' : 'csp-upload-body--single'}`}>
          {/* LEFT: generate from a pose (the path most people want) */}
          {showPoseOption && (
            <div className="csp-upload-slot">
              <div className="csp-upload-slot-label">From Pose</div>
              <div
                className="csp-upload-pose-card"
                onClick={() => { handleCancel(); onOpenPoseManager(); }}
              >
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="5" r="2"></circle>
                  <path d="M12 7v5"></path>
                  <path d="M9 22l3-6 3 6"></path>
                  <path d="M7 12l5 2 5-2"></path>
                </svg>
                <strong>Generate from a Pose</strong>
                <small>Pose the 3D model and render portraits for any of your skins</small>
              </div>
            </div>
          )}

          <div className="csp-upload-slot">
            <div className="csp-upload-slot-label">{showPoseOption ? 'Upload Image' : 'Portrait Image'}</div>
            <div
              className={`csp-upload-slot-preview ${preview ? 'has-image' : ''}`}
              onClick={() => document.getElementById('csp-upload-input').click()}
            >
              {preview ? (
                <img src={preview} alt="Portrait preview" />
              ) : existingNormalUrl ? (
                <>
                  <img src={existingNormalUrl} alt="Current portrait" className="csp-upload-existing" />
                  <div className="csp-upload-slot-overlay">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="17 8 12 3 7 8"></polyline>
                      <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                    <span>Click to replace</span>
                  </div>
                </>
              ) : (
                <div className="csp-upload-slot-empty">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                  <span>Click to upload</span>
                </div>
              )}
              {preview && (
                <button
                  className="csp-upload-slot-clear"
                  onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              )}
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="csp-upload-input"
            />
            <p className="csp-upload-note">
              One image is all you need — it's scaled down for the game, and a
              high-res copy is kept for HD previews when the image is big enough.
            </p>
          </div>
        </div>

        <div className="csp-upload-actions">
          <button className="csp-upload-btn csp-upload-btn--cancel" onClick={handleCancel}>
            Cancel
          </button>
          <button
            className="csp-upload-btn csp-upload-btn--confirm"
            onClick={handleConfirm}
            disabled={!file}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            {uploadTarget === 'main' ? 'Replace' : 'Add'}
          </button>
        </div>
      </div>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}

export default function CspManagerModal({
  show,
  cspManagerSkin,
  pendingMainCspPreview,
  hdCspInfo,
  compareSliderPosition,
  lastImageUpdate,
  alternativeCsps,
  capturingHdCsp,
  onClose,
  onCspManagerMainChange,
  onCompareSliderStart,
  onSwapCsp,
  onRemoveAlternativeCsp,
  onAddAlternativeCsp,
  onCaptureHdCsp,
  onRegenerateAltHd,
  onResetToOriginal,
  onOpenPoseManager,
  onSave,
  onUploadMainCsp,    // ({ normalFile, hdFile }) => void
  onUploadAltCsp,     // ({ normalFile, hdFile }) => void
  API_URL
}) {
  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [uploadTarget, setUploadTarget] = useState(null) // 'main' or 'alt'

  if (!show || !cspManagerSkin) return null

  // Handlers for opening upload modal
  const handleReplaceClick = () => {
    setUploadTarget('main')
    setUploadModalOpen(true)
  }

  const handleAddClick = () => {
    setUploadTarget('alt')
    setUploadModalOpen(true)
  }

  const handleUploadConfirm = ({ file }) => {
    if (uploadTarget === 'main' && onUploadMainCsp) {
      onUploadMainCsp({ file })
    } else if (uploadTarget === 'alt' && onUploadAltCsp) {
      onUploadAltCsp({ file })
    }
    setUploadModalOpen(false)
    setUploadTarget(null)
  }

  const handleUploadCancel = () => {
    setUploadModalOpen(false)
    setUploadTarget(null)
  }

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

    // Pose-less alts only group with themselves (null poseName must not
    // cross-match other null-poseName alts)
    const nonHd = alt.poseName
      ? alternativeCsps.find(a => a.poseName === alt.poseName && !a.isHd)
      : (!alt.isHd ? alt : null)
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
  const mainPoseName = !isAltActive ? cspManagerSkin.csp_pose_name : null

  const handleClose = () => {
    playSound('back')
    onClose()
  }

  const modal = (
    <div className="csp-manager-overlay" onClick={handleClose}>
      <div className="csp-manager-modal" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="csp-manager-close" onClick={handleClose} title="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {/* Header */}
        <div className="csp-manager-header">
          <div className="csp-manager-header-title">
            <h2>CSP Manager</h2>
            <span className="csp-manager-skin-name">{cspManagerSkin.color}</span>
          </div>
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
              {mainPoseName && (
                <span className="csp-manager-main-pose-badge">
                  {mainPoseName}
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
              <button
                className="csp-manager-main-replace-btn"
                onClick={handleReplaceClick}
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

          {/* Right: Portraits Grid (original + alternatives, active highlighted) */}
          <div className="csp-manager-alternatives">
            <div className="csp-manager-alternatives-header">
              <span>Portraits</span>
              <span className="csp-manager-alternatives-count">
                ({groupedAlts.length + (cspManagerSkin.has_csp ? 1 : 0)})
              </span>
              <span className="csp-manager-alternatives-hint">Click a portrait to make it active</span>
            </div>
            <div className="csp-manager-alternatives-grid">
              {/* Original CSP - always shown, just another portrait */}
              {cspManagerSkin.has_csp && (
                <div
                  className={`csp-manager-alt-card csp-manager-alt-card--original ${!isAltActive ? 'csp-manager-alt-card--active' : ''}`}
                  onClick={() => isAltActive && onResetToOriginal && onResetToOriginal()}
                >
                  <img
                    src={`${cspManagerSkin.cspUrl}?t=${lastImageUpdate}`}
                    alt="Original CSP"
                    className="csp-manager-alt-image"
                  />
                  <div className="csp-manager-alt-badges">
                    {!isAltActive ? (
                      <div className="csp-manager-alt-active-badge">Active</div>
                    ) : (
                      <div className="csp-manager-alt-original-badge">Original</div>
                    )}
                    {hdCspInfo?.exists && (
                      <div className="csp-manager-alt-hd-badge">HD</div>
                    )}
                  </div>
                  <div className="csp-manager-alt-pose-label">{cspManagerSkin.csp_pose_name || 'Original'}</div>
                  {isAltActive && (
                    <div className="csp-manager-alt-overlay">
                      <span>Set Active</span>
                    </div>
                  )}
                </div>
              )}
              {groupedAlts.map((group) => {
                const displayAlt = group.displayAlt
                if (!displayAlt) return null

                return (
                  <div
                    key={group.poseName || displayAlt.id}
                    className={`csp-manager-alt-card ${group.isActive ? 'csp-manager-alt-card--active' : ''}`}
                    onClick={() => !group.isActive && onSwapCsp(group.swapIndex)}
                  >
                    <img src={displayAlt.url} alt={group.poseName || 'Alternative'} className="csp-manager-alt-image" />
                    <div className="csp-manager-alt-badges">
                      {group.isActive && (
                        <div className="csp-manager-alt-active-badge">Active</div>
                      )}
                      {group.hd && (
                        <div className="csp-manager-alt-hd-badge">HD</div>
                      )}
                    </div>
                    {/* Pose name label */}
                    {group.poseName && (
                      <div className="csp-manager-alt-pose-label">{group.poseName}</div>
                    )}
                    {!group.isActive && (
                      <div className="csp-manager-alt-overlay">
                        <span>Set Active</span>
                      </div>
                    )}
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
              <div className="csp-manager-add-card" onClick={handleAddClick}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>Add CSP</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar: pose manager (left) + HD capture, always 4x (right) */}
        <div className="csp-manager-hd-section">
          {onOpenPoseManager && (
            <button
              className="csp-manager-poses-btn"
              onClick={onOpenPoseManager}
              title="Pose the 3D model and batch-render portraits from it"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="5" r="2"></circle>
                <path d="M12 7v5"></path>
                <path d="M9 22l3-6 3 6"></path>
                <path d="M7 12l5 2 5-2"></path>
              </svg>
              Manage Poses
            </button>
          )}
          <div className="csp-manager-hd-controls">
            {hasActiveHd ? (
              <span className="csp-manager-hd-badge">
                HD {isAltActive ? '' : (hdCspInfo?.size || hdCspInfo?.resolution || '')}
              </span>
            ) : (
              <span className="csp-manager-hd-hint">
                Re-renders the active portrait at 4x
              </span>
            )}
            <button
              className="csp-manager-hd-capture-btn"
              onClick={onCaptureHdCsp}
              disabled={capturingHdCsp}
              title="Re-render the active portrait at 4x resolution"
            >
              {capturingHdCsp ? (
                <>
                  <span className="csp-manager-spinner"></span>
                  Generating...
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                  {hasActiveHd ? 'Regenerate HD' : 'Generate HD'}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="csp-manager-actions">
          <button className="csp-manager-btn csp-manager-btn--cancel" onClick={handleClose}>
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

        {/* Upload Modal */}
        <CspUploadModal
          show={uploadModalOpen}
          uploadTarget={uploadTarget}
          existingNormalUrl={uploadTarget === 'main' ? activeDisplayUrl : null}
          onConfirm={handleUploadConfirm}
          onCancel={handleUploadCancel}
          onOpenPoseManager={onOpenPoseManager}
        />
      </div>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}
