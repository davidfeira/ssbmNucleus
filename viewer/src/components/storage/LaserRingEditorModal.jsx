import { useState, useEffect } from 'react'

/**
 * LaserRingEditorModal - Color picker UI for creating/editing laser ring mods
 * Used for Fox/Falco laser hit ring effect
 * Two RGB colors + hue index bytes (auto-zeroed)
 */

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

const SaveIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
    <polyline points="17 21 17 13 7 13 7 21"/>
    <polyline points="7 3 7 8 15 8"/>
  </svg>
)

// Color presets
const COLOR_PRESETS = [
  { name: 'Red', hex: '#FF0000' },
  { name: 'Blue', hex: '#0066FF' },
  { name: 'Green', hex: '#00FF00' },
  { name: 'Yellow', hex: '#FFFF00' },
  { name: 'Magenta', hex: '#FF00FF' },
  { name: 'Cyan', hex: '#00FFFF' },
  { name: 'Orange', hex: '#FF6600' },
  { name: 'Purple', hex: '#9900FF' },
  { name: 'White', hex: '#FFFFFF' },
  { name: 'Pink', hex: '#FF66CC' }
]

// Default colors (vanilla laser ring)
const DEFAULT_COLOR1 = 'FF004C'
const DEFAULT_COLOR2 = 'B20000'

// Convert hex to display format
function toDisplayHex(rgb) {
  if (!rgb || rgb.length < 6) return '#FF004C'
  return `#${rgb.slice(0, 6)}`
}

// Convert display hex to RGB storage format
function toStorageRgb(hex) {
  return hex.replace('#', '').toUpperCase()
}

// Darken a color by a percentage
function darkenColor(hex, percent) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, Math.floor((num >> 16) * (1 - percent)))
  const g = Math.max(0, Math.floor(((num >> 8) & 0x00FF) * (1 - percent)))
  const b = Math.max(0, Math.floor((num & 0x0000FF) * (1 - percent)))
  return ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0').toUpperCase()
}

// RGB color picker
function ColorPicker({ label, description, value, onChange }) {
  const displayHex = toDisplayHex(value)

  const handleChange = (e) => {
    onChange(toStorageRgb(e.target.value))
  }

  return (
    <div className="laser-color-picker">
      <div className="laser-color-header">
        <span className="laser-color-label">{label}</span>
        <span className="laser-color-description">{description}</span>
      </div>

      <div className="laser-color-controls">
        <div className="laser-color-input-group">
          <input
            type="color"
            value={displayHex}
            onChange={handleChange}
            className="laser-color-input"
          />
          <div className="laser-color-values">
            <span className="laser-color-hex">{displayHex.toUpperCase()}</span>
            <span className="laser-color-rgby">RGB: {value || DEFAULT_COLOR1}</span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.map((preset) => (
            <button
              key={preset.name}
              className={`laser-preset ${displayHex.toUpperCase() === preset.hex.toUpperCase() ? 'active' : ''}`}
              style={{ backgroundColor: preset.hex }}
              onClick={() => onChange(toStorageRgb(preset.hex))}
              title={preset.name}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function LaserRingEditorModal({
  show,
  character,
  extraType,
  editingMod,
  onClose,
  onSave,
  onDelete,
  API_URL
}) {
  const [name, setName] = useState('')
  const [color1, setColor1] = useState(DEFAULT_COLOR1)
  const [color2, setColor2] = useState(DEFAULT_COLOR2)
  const [linkColors, setLinkColors] = useState(true) // Auto-derive color2 from color1
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod or vanilla
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications?.color1?.color) {
        setColor1(editingMod.modifications.color1.color)
      }
      if (editingMod.modifications?.color2?.color) {
        setColor2(editingMod.modifications.color2.color)
      }
      setLinkColors(false) // Don't auto-link when editing
    } else {
      // Reset for new mod - use vanilla colors
      setName('')
      setColor1(extraType?.vanilla?.color1 || DEFAULT_COLOR1)
      setColor2(extraType?.vanilla?.color2 || DEFAULT_COLOR2)
      setLinkColors(true)
    }
    setError(null)
  }, [editingMod, show, extraType])

  // Auto-derive color2 when color1 changes and linked
  useEffect(() => {
    if (linkColors) {
      setColor2(darkenColor(color1, 0.3))
    }
  }, [color1, linkColors])

  if (!show) return null

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Please enter a name for this mod')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const modData = {
        character,
        extraType: extraType.id,
        name: name.trim(),
        modifications: {
          color1: { color: color1 },
          color2: { color: color2 },
          // Set all hue bytes to 00 for custom colors
          hue1: { color: '00' },
          hue2: { color: '00' },
          hue3: { color: '00' },
          hue4: { color: '00' },
          hue5: { color: '00' },
          hue6: { color: '00' }
        }
      }

      if (editingMod) {
        modData.modId = editingMod.id
      }

      const response = await fetch(`${API_URL}/storage/extras/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modData)
      })

      const data = await response.json()
      if (data.success) {
        onSave?.(data.mod)
        onClose()
      } else {
        setError(data.error || 'Failed to save mod')
      }
    } catch (err) {
      console.error('[LaserRingEditorModal] Save error:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!editingMod) return
    if (!confirm(`Delete "${editingMod.name}"?`)) return

    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/storage/extras/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          extraType: extraType.id,
          modId: editingMod.id
        })
      })
      const data = await response.json()
      if (data.success) {
        onDelete?.(editingMod.id)
        onClose()
      } else {
        setError(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      setError(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
    }
  }

  const displayHex1 = toDisplayHex(color1)
  const displayHex2 = toDisplayHex(color2)

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Laser Ring' : 'Create Laser Ring'}
            </span>
            <span className="laser-editor-title-char">{character}</span>
          </div>
          <button className="laser-editor-close" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="laser-editor-body">
          {/* Name input */}
          <div className="laser-editor-name-group">
            <label className="laser-editor-name-label">Mod Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Green Ring, Blue Hit..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview - laser ring visualization */}
          <div className="laser-preview">
            <div className="laser-preview-label">Preview</div>
            <div className="laser-preview-display" style={{ background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)' }}>
              <div style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {/* Outer glow - secondary color */}
                <div
                  style={{
                    position: 'absolute',
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: `radial-gradient(ellipse at center, ${displayHex2}40 0%, transparent 70%)`,
                    filter: `drop-shadow(0 0 12px ${displayHex2}50)`
                  }}
                />
                {/* Main ring - primary color */}
                <div
                  style={{
                    position: 'absolute',
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    border: `4px solid ${displayHex1}`,
                    boxShadow: `0 0 12px ${displayHex1}, inset 0 0 12px ${displayHex1}40`
                  }}
                />
                {/* Inner ring - primary color */}
                <div
                  style={{
                    position: 'absolute',
                    width: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    border: `3px solid ${displayHex1}`,
                    opacity: 0.6
                  }}
                />
                {/* Center dot - primary color */}
                <div
                  style={{
                    position: 'absolute',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: displayHex1,
                    boxShadow: `0 0 6px ${displayHex1}`
                  }}
                />
              </div>
            </div>
          </div>

          {/* Color pickers */}
          <ColorPicker
            label="Primary Color"
            description="Main ring color"
            value={color1}
            onChange={(c) => {
              setColor1(c)
            }}
          />

          {/* Link toggle */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 0', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={linkColors}
              onChange={(e) => setLinkColors(e.target.checked)}
            />
            <span style={{ fontSize: '12px', color: '#888' }}>Auto-derive secondary color (darker)</span>
          </label>

          {!linkColors && (
            <ColorPicker
              label="Secondary Color"
              description="Outer glow color"
              value={color2}
              onChange={setColor2}
            />
          )}

          {error && (
            <div className="laser-editor-error">{error}</div>
          )}
        </div>

        <div className="laser-editor-footer">
          {editingMod && (
            <button
              className="laser-editor-delete"
              onClick={handleDelete}
              disabled={deleting || saving}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          )}
          <div className="laser-editor-footer-right">
            <button className="laser-editor-cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              className="laser-editor-save"
              onClick={handleSave}
              disabled={saving || deleting}
            >
              <SaveIcon />
              <span>{saving ? 'Saving...' : 'Save Mod'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
