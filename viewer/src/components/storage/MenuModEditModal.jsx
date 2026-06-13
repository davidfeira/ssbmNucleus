/**
 * MenuModEditModal - the edit modal for a menu / HUD mod card.
 *
 * Opened by the big pencil on a MenuModGrid card. Mirrors the costume/stage
 * EditModal: a framed preview on the left, a name field + per-type action
 * buttons (Edit Textures, Capture Screenshot, Manage Icons, scene toggle…) on
 * the right, and a Save / Delete / Cancel bar at the bottom. The texture
 * editors themselves open as their own separate screen from the "Edit"
 * action — this modal is just the hub.
 *
 * It's presentational and config-driven (like MenuModGrid): each view supplies
 * the preview shape, the action list, and the save/delete handlers.
 */
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { getAppContentPortalTarget } from './appContentPortal'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function MenuModEditModal({
  show,
  title = 'Edit Mod',
  previewUrl,
  thumb = 'wide',                 // 'wide' | 'tall' | 'square'
  imgFit = 'contain',             // 'contain' | 'cover' | 'fill'
  name,
  onNameChange,
  nameLabel = 'Name',
  actions = [],                   // [{ key, label, icon, title, onClick, disabled }]
  extra,                          // node rendered under the actions (e.g. toggle)
  editableImage = false,          // show the image-replace pencil overlay
  imagePreview = null,            // pending replacement image (data URL)
  onImageChange,                  // file input handler
  imageEditTitle = 'Replace image',
  saving = false,
  deleting = false,
  exporting = false,
  saveLabel = 'Save',
  onSave,
  onExport,
  onDelete,
  onCancel,
}) {
  const [monogramOnly, setMonogramOnly] = useState(false)

  useEffect(() => { setMonogramOnly(!previewUrl) }, [previewUrl])

  if (!show) return null

  const busy = saving || deleting || exporting
  const fileInputId = 'mmod-image-input'

  const handleCancel = () => { playSound('back'); onCancel?.() }

  const modal = (
    <div className="edit-modal-fullscreen-overlay" onClick={handleCancel}>
      <div className="edit-modal-fullscreen" onClick={(e) => e.stopPropagation()}>
        <button className="edit-modal-close" onClick={handleCancel} title="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        <div className="edit-modal-header">
          <h2>{title}</h2>
        </div>

        <div className="edit-modal-body">
          {/* LEFT: framed preview (reuses the grid thumbnail styling so doors
              stay 128x200 / stretched, screenshots crop, glyph sheets letterbox) */}
          <div className="edit-modal-csp-section">
            <div className={`mmod-thumb mmod-thumb--${thumb} mmod-thumb--fit-${imgFit} mmod-modal-thumb`}>
              <span className="mmod-monogram">{(name || '?')[0]}</span>
              {imagePreview ? (
                <img src={imagePreview} alt="New preview" />
              ) : (!monogramOnly && previewUrl) ? (
                <img
                  src={previewUrl}
                  alt={name}
                  onError={() => setMonogramOnly(true)}
                />
              ) : null}

              {editableImage && (
                <>
                  <input
                    type="file"
                    accept="image/*"
                    id={fileInputId}
                    style={{ display: 'none' }}
                    onChange={onImageChange}
                  />
                  <button
                    className="edit-modal-image-edit-btn"
                    onClick={() => document.getElementById(fileInputId)?.click()}
                    title={imageEditTitle}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>Edit Image</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* RIGHT: name + actions */}
          <div className="edit-modal-controls-section edit-modal-controls-section--wide">
            <div className="edit-modal-field">
              <label>{nameLabel}</label>
              <input
                type="text"
                value={name}
                onChange={(e) => onNameChange?.(e.target.value)}
                placeholder="Enter name..."
                disabled={busy}
                autoFocus
              />
            </div>

            {actions.length > 0 && (
              <div className="mmod-modal-actions">
                {actions.map((a) => (
                  <button
                    key={a.key}
                    className="edit-modal-view3d-btn"
                    onMouseEnter={playHoverSound}
                    onClick={() => { if (a.disabled) return; playSound('boop'); a.onClick?.() }}
                    disabled={busy || a.disabled}
                    title={a.title}
                  >
                    {a.icon}
                    <span>{a.label}</span>
                  </button>
                ))}
              </div>
            )}

            {extra && <div className="mmod-modal-extra">{extra}</div>}
          </div>
        </div>

        {/* Bottom Action Bar */}
        <div className="edit-modal-actions">
          {onSave && (
            <button
              className="edit-modal-action-btn edit-modal-action-btn--save"
              onClick={() => { playSound('boop'); onSave() }}
              disabled={busy}
            >
              {saving ? (
                <><span className="edit-modal-action-spinner"></span>Saving...</>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                  </svg>
                  {saveLabel}
                </>
              )}
            </button>
          )}
          {onExport && (
            <button
              className="edit-modal-action-btn edit-modal-action-btn--export"
              onClick={() => { playSound('boop'); onExport() }}
              disabled={busy}
            >
              {exporting ? (
                <><span className="edit-modal-action-spinner"></span>Exporting...</>
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
          )}
          {onDelete && (
            <button
              className="edit-modal-action-btn edit-modal-action-btn--delete"
              onClick={() => { playSound('boop'); onDelete() }}
              disabled={busy}
            >
              {deleting ? (
                <><span className="edit-modal-action-spinner"></span>Deleting...</>
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
          )}
          <button
            className="edit-modal-action-btn edit-modal-action-btn--cancel"
            onClick={handleCancel}
            disabled={busy}
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

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}
