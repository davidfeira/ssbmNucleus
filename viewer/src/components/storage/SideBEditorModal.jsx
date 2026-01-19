import { useState, useEffect } from 'react'

/**
 * SideBEditorModal - Color picker UI for creating/editing side-B mods
 * Allows setting colors for each afterimage layer (primary, secondary, tertiary)
 * Uses RGBA format (8 hex chars) instead of RGBY
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

// Color presets for quick selection (RGBA format with full alpha)
const COLOR_PRESETS = [
  { name: 'Blue', rgba: '0099FFFF', hex: '#0099FF' },
  { name: 'Red', rgba: 'FF0000FF', hex: '#FF0000' },
  { name: 'Green', rgba: '00FF00FF', hex: '#00FF00' },
  { name: 'Yellow', rgba: 'FFFF00FF', hex: '#FFFF00' },
  { name: 'Magenta', rgba: 'FF00FFFF', hex: '#FF00FF' },
  { name: 'Cyan', rgba: '00FFFFFF', hex: '#00FFFF' },
  { name: 'Orange', rgba: 'FF6600FF', hex: '#FF6600' },
  { name: 'Purple', rgba: '9900FFFF', hex: '#9900FF' },
  { name: 'White', rgba: 'FFFFFFFF', hex: '#FFFFFF' },
  { name: 'Pink', rgba: 'FF99CCFF', hex: '#FF99CC' }
]

// Convert RGBA hex string to display hex (#RRGGBB)
function rgbaToHex(rgba) {
  if (!rgba || rgba.length < 6) return '#0099FF'
  return `#${rgba.substring(0, 6)}`
}

// Convert hex color to RGBA (with full alpha)
function hexToRgba(hex) {
  const clean = hex.replace('#', '').toUpperCase()
  return clean.length === 6 ? `${clean}FF` : clean
}

function RgbaColorPicker({ label, description, value, onChange }) {
  // Handle undefined or invalid values
  const safeValue = value || '0099FFFF'
  const hexValue = rgbaToHex(safeValue)

  const handleHexChange = (e) => {
    const hex = e.target.value
    onChange(hexToRgba(hex))
  }

  const handlePresetClick = (preset) => {
    onChange(preset.rgba)
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
            value={hexValue}
            onChange={handleHexChange}
            className="laser-color-input"
          />
          <div className="laser-color-values">
            <span className="laser-color-hex">{hexValue.toUpperCase()}</span>
            <span className="laser-color-rgby">RGBA: {safeValue}</span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.map((preset) => (
            <button
              key={preset.name}
              className={`laser-preset ${safeValue === preset.rgba ? 'active' : ''}`}
              style={{ backgroundColor: preset.hex }}
              onClick={() => handlePresetClick(preset)}
              title={preset.name}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function SideBEditorModal({
  show,
  character,
  extraType,
  editingMod,
  onClose,
  onSave,
  API_URL
}) {
  const [name, setName] = useState('')
  const [colors, setColors] = useState({
    primary: '0099FFFF',
    secondary: 'CCE6FFFF',
    tertiary: 'FFFFFFFF'
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod if provided
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          primary: editingMod.modifications.primary?.color || '0099FFFF',
          secondary: editingMod.modifications.secondary?.color || 'CCE6FFFF',
          tertiary: editingMod.modifications.tertiary?.color || 'FFFFFFFF'
        })
      }
    } else {
      // Reset for new mod
      setName('')
      setColors({ primary: '0099FFFF', secondary: 'CCE6FFFF', tertiary: 'FFFFFFFF' })
    }
    setError(null)
  }, [editingMod, show])

  if (!show) return null

  const handleColorChange = (layer, rgba) => {
    setColors(prev => ({ ...prev, [layer]: rgba }))
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
          primary: { color: colors.primary },
          secondary: { color: colors.secondary },
          tertiary: { color: colors.tertiary }
        }
      }

      // If editing, include the mod ID
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
      console.error('[SideBEditorModal] Save error:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleApplyToAll = (rgba) => {
    setColors({
      primary: rgba,
      secondary: rgba,
      tertiary: rgba
    })
  }

  // Get display colors for preview
  const primaryHex = rgbaToHex(colors.primary)
  const secondaryHex = rgbaToHex(colors.secondary)
  const tertiaryHex = rgbaToHex(colors.tertiary)

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Side-B Mod' : 'Create Side-B Mod'}
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
              placeholder="e.g., Red Phantasm, Blue Illusion..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview - afterimage visualization */}
          <div className="laser-preview">
            <div className="laser-preview-label">Preview</div>
            <div className="laser-preview-display" style={{ background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)' }}>
              {/* Afterimage trail */}
              {[0.15, 0.3, 0.5, 0.7].map((opacity, i) => (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    left: `${10 + i * 18}%`,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '24px',
                    height: '36px',
                    borderRadius: '4px',
                    background: `linear-gradient(135deg, ${primaryHex} 0%, ${secondaryHex} 50%, ${tertiaryHex} 100%)`,
                    opacity: opacity,
                    boxShadow: `0 0 ${8 + i * 4}px ${primaryHex}40`
                  }}
                />
              ))}
              {/* Main silhouette */}
              <div
                style={{
                  position: 'absolute',
                  right: '12%',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: '28px',
                  height: '40px',
                  borderRadius: '4px',
                  background: `linear-gradient(135deg, ${primaryHex} 0%, ${secondaryHex} 50%, ${tertiaryHex} 100%)`,
                  boxShadow: `0 0 12px ${primaryHex}60, 0 0 20px ${secondaryHex}40`
                }}
              />
            </div>
          </div>

          {/* Color pickers for each layer */}
          {extraType.properties.map((prop) => (
            <RgbaColorPicker
              key={prop.id}
              label={prop.name}
              description={prop.description}
              value={colors[prop.id]}
              onChange={(value) => handleColorChange(prop.id, value)}
            />
          ))}

          {/* Quick apply to all */}
          <div className="laser-apply-all">
            <span className="laser-apply-all-label">Apply to all layers:</span>
            <div className="laser-apply-all-presets">
              {COLOR_PRESETS.slice(0, 6).map((preset) => (
                <button
                  key={preset.name}
                  className="laser-apply-preset"
                  style={{ backgroundColor: preset.hex }}
                  onClick={() => handleApplyToAll(preset.rgba)}
                  title={`Set all to ${preset.name}`}
                />
              ))}
            </div>
          </div>

          {error && (
            <div className="laser-editor-error">{error}</div>
          )}
        </div>

        <div className="laser-editor-footer">
          <button className="laser-editor-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="laser-editor-save"
            onClick={handleSave}
            disabled={saving}
          >
            <SaveIcon />
            <span>{saving ? 'Saving...' : 'Save Mod'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
