import { useState, useEffect } from 'react'

/**
 * DualColorEditorModal - Color picker UI for creating/editing 2-color effect mods
 * Used for Falcon Punch, Warlock Punch, Thunder, Fireballs, Shadow Ball, PK Thunder
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

// Get preview component based on extra type
function EffectPreview({ extraType, colors }) {
  const color1Hex = toDisplayHex(colors.color1 || colors.tip_color1)
  const color2Hex = toDisplayHex(colors.color2 || colors.tip_color2)

  // Punch effect - fist with flame
  if (extraType?.id === 'falcon_punch' || extraType?.id === 'warlock_punch') {
    return (
      <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
        {/* Outer flame glow */}
        <ellipse cx="60" cy="30" rx="50" ry="25" fill={color2Hex} opacity="0.3" />
        {/* Inner flame */}
        <ellipse cx="60" cy="30" rx="35" ry="18" fill={color1Hex} opacity="0.7" />
        {/* Core */}
        <ellipse cx="60" cy="30" rx="20" ry="10" fill={color1Hex} />
      </svg>
    )
  }

  // Thunder effect - lightning bolt
  if (extraType?.id === 'thunder' || extraType?.id === 'pk_thunder') {
    return (
      <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
        {/* Outer glow */}
        <path d="M60 5 L45 25 L55 25 L40 55 L75 30 L62 30 L80 5 Z"
          fill={color2Hex} opacity="0.4" transform="scale(1.1) translate(-6, -3)" />
        {/* Lightning bolt */}
        <path d="M60 5 L45 25 L55 25 L40 55 L75 30 L62 30 L80 5 Z"
          fill={color1Hex} />
      </svg>
    )
  }

  // Fireball effect - circle with glow
  if (extraType?.id === 'fireball') {
    return (
      <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
        {/* Outer glow */}
        <circle cx="60" cy="30" r="28" fill={color2Hex} opacity="0.4" />
        {/* Mid glow */}
        <circle cx="60" cy="30" r="20" fill={color1Hex} opacity="0.7" />
        {/* Core */}
        <circle cx="60" cy="30" r="12" fill={color1Hex} />
      </svg>
    )
  }

  // Shadow Ball effect - dark orb
  if (extraType?.id === 'shadow_ball') {
    return (
      <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
        {/* Outer energy */}
        <circle cx="60" cy="30" r="28" fill={color2Hex} opacity="0.3" />
        {/* Inner sphere */}
        <circle cx="60" cy="30" r="20" fill={color1Hex} opacity="0.6" />
        {/* Core */}
        <circle cx="60" cy="30" r="10" fill={color1Hex} />
      </svg>
    )
  }

  // Default dual-color preview
  return (
    <svg width="120" height="60" viewBox="0 0 120 60" style={{ overflow: 'visible' }}>
      <circle cx="40" cy="30" r="20" fill={color1Hex} />
      <circle cx="80" cy="30" r="20" fill={color2Hex} />
    </svg>
  )
}

export default function DualColorEditorModal({
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
  const [colors, setColors] = useState({})
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  // Get color keys from extraType properties
  const colorKeys = extraType?.properties?.map(p => p.id) || ['color1', 'color2']

  // Initialize from editing mod or vanilla
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        const newColors = {}
        colorKeys.forEach(key => {
          newColors[key] = editingMod.modifications[key]?.color || extraType?.vanilla?.[key] || 'FFFFFF'
        })
        setColors(newColors)
      }
    } else {
      // Reset for new mod - use vanilla colors from extraType
      setName('')
      const vanilla = extraType?.vanilla || {}
      const newColors = {}
      colorKeys.forEach(key => {
        newColors[key] = vanilla[key] || 'FFFFFF'
      })
      setColors(newColors)
    }
    setError(null)
  }, [editingMod, show, extraType])

  if (!show) return null

  const handleColorChange = (key, value) => {
    setColors(prev => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Please enter a name for this mod')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const modifications = {}
      // Set the main color properties
      colorKeys.forEach(key => {
        modifications[key] = { color: colors[key] }
      })

      // For effects with multiple offsets (like Falcon Punch), set all related offsets
      // Any offset ending in _c1 gets color1, any offset ending in _c2 gets color2
      if (extraType?.offsets) {
        const allOffsetKeys = Object.keys(extraType.offsets)
        allOffsetKeys.forEach(key => {
          if (key.endsWith('_c1') && colors.color1) {
            modifications[key] = { color: colors.color1 }
          } else if (key.endsWith('_c2') && colors.color2) {
            modifications[key] = { color: colors.color2 }
          }
        })
      }

      const modData = {
        character,
        extraType: extraType.id,
        name: name.trim(),
        modifications
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
      console.error('[DualColorEditorModal] Save error:', err)
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

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? `Edit ${extraType?.name || 'Effect'}` : `Create ${extraType?.name || 'Effect'}`}
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
              placeholder={`e.g., Blue ${extraType?.name || 'Effect'}...`}
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview */}
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
                <EffectPreview extraType={extraType} colors={colors} />
              </div>
            </div>
          </div>

          {/* Color pickers for each property */}
          {extraType?.properties?.map((prop) => (
            <ColorPicker
              key={prop.id}
              label={prop.name}
              description={prop.description}
              value={colors[prop.id]}
              onChange={(value) => handleColorChange(prop.id, value)}
            />
          ))}

          {/* Quick apply presets */}
          <div className="laser-apply-all">
            <span className="laser-apply-all-label">Quick presets:</span>
            <div className="laser-apply-all-presets">
              {COLOR_PRESETS.slice(0, 6).map((preset) => (
                <button
                  key={preset.name}
                  className="laser-apply-preset"
                  style={{ backgroundColor: preset.hex }}
                  onClick={() => {
                    // Set primary color to preset
                    const primaryKey = colorKeys[0]
                    handleColorChange(primaryKey, toStorageRgb(preset.hex))
                  }}
                  title={`Set primary to ${preset.name}`}
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
