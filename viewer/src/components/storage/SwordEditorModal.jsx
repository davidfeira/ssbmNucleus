import { useState, useEffect } from 'react'

/**
 * SwordEditorModal - Color picker UI for creating/editing sword trail mods
 * Used for Marth, Roy, Link, Young Link sword swing colors
 * 3x RGB colors: main, secondary, tertiary (edge)
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

// Default colors (Marth vanilla)
const DEFAULT_COLORS = {
  main: 'FF0000',
  secondary: 'FFFF00',
  tertiary: 'FFFFFF'
}

// Convert hex to display format
function toDisplayHex(rgb) {
  if (!rgb || rgb.length < 6) return '#FF0000'
  return `#${rgb.slice(0, 6)}`
}

// Convert display hex to RGB storage format
function toStorageRgb(hex) {
  return hex.replace('#', '').toUpperCase()
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
            <span className="laser-color-rgby">RGB: {value || 'FF0000'}</span>
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

export default function SwordEditorModal({
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
  const [colors, setColors] = useState({ ...DEFAULT_COLORS })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod or vanilla
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          main: editingMod.modifications.main?.color || DEFAULT_COLORS.main,
          secondary: editingMod.modifications.secondary?.color || DEFAULT_COLORS.secondary,
          tertiary: editingMod.modifications.tertiary?.color || DEFAULT_COLORS.tertiary
        })
      }
    } else {
      // Reset for new mod - use vanilla colors from extraType if available
      setName('')
      const vanilla = extraType?.vanilla || DEFAULT_COLORS
      setColors({
        main: vanilla.main || DEFAULT_COLORS.main,
        secondary: vanilla.secondary || DEFAULT_COLORS.secondary,
        tertiary: vanilla.tertiary || DEFAULT_COLORS.tertiary
      })
    }
    setError(null)
  }, [editingMod, show, extraType])

  if (!show) return null

  const handleColorChange = (layer, value) => {
    setColors(prev => ({ ...prev, [layer]: value }))
  }

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
          main: { color: colors.main },
          secondary: { color: colors.secondary },
          tertiary: { color: colors.tertiary }
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
      console.error('[SwordEditorModal] Save error:', err)
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

  // Apply preset to all layers as gradient
  const handleApplyGradient = (preset) => {
    setColors({
      main: toStorageRgb(preset.hex),
      secondary: 'FFFF00', // Keep yellow middle
      tertiary: 'FFFFFF'   // Keep white edge
    })
  }

  // Apply same color to all
  const handleApplyToAll = (preset) => {
    const rgb = toStorageRgb(preset.hex)
    setColors({
      main: rgb,
      secondary: rgb,
      tertiary: rgb
    })
  }

  // Get display colors for preview
  const mainHex = toDisplayHex(colors.main)
  const secondaryHex = toDisplayHex(colors.secondary)
  const tertiaryHex = toDisplayHex(colors.tertiary)

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Sword Trail' : 'Create Sword Trail'}
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
              placeholder="e.g., Blue Sword, Ice Trail..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview - sword trail visualization */}
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
                {/* Sword trail arc */}
                <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
                  {/* Outer edge (tertiary) */}
                  <path
                    d="M 10 50 Q 60 -10 110 50"
                    fill="none"
                    stroke={tertiaryHex}
                    strokeWidth="16"
                    strokeLinecap="round"
                    opacity="0.5"
                  />
                  {/* Middle (secondary) */}
                  <path
                    d="M 10 50 Q 60 -10 110 50"
                    fill="none"
                    stroke={secondaryHex}
                    strokeWidth="10"
                    strokeLinecap="round"
                    opacity="0.7"
                  />
                  {/* Inner core (main) */}
                  <path
                    d="M 10 50 Q 60 -10 110 50"
                    fill="none"
                    stroke={mainHex}
                    strokeWidth="4"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Color pickers */}
          <ColorPicker
            label="Main"
            description="Primary trail color (inner)"
            value={colors.main}
            onChange={(value) => handleColorChange('main', value)}
          />

          <ColorPicker
            label="Secondary"
            description="Middle gradient color"
            value={colors.secondary}
            onChange={(value) => handleColorChange('secondary', value)}
          />

          <ColorPicker
            label="Edge"
            description="Outer edge color"
            value={colors.tertiary}
            onChange={(value) => handleColorChange('tertiary', value)}
          />

          {/* Quick apply */}
          <div className="laser-apply-all">
            <span className="laser-apply-all-label">Set main color:</span>
            <div className="laser-apply-all-presets">
              {COLOR_PRESETS.slice(0, 6).map((preset) => (
                <button
                  key={preset.name}
                  className="laser-apply-preset"
                  style={{ backgroundColor: preset.hex }}
                  onClick={() => handleApplyGradient(preset)}
                  title={`Set main to ${preset.name}`}
                />
              ))}
            </div>
          </div>

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
