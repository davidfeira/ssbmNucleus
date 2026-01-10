import { useState, useEffect } from 'react'
import { hexToRgby, rgbyToHex, RGBY_PRESETS, formatRgby } from '../../utils/rgbyColor'

/**
 * LaserEditorModal - Color picker UI for creating/editing laser mods
 * Allows setting colors for each laser layer (wide, thin, outline)
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

// Color presets for quick selection
const COLOR_PRESETS = [
  { name: 'Red', rgby: 'FC00', hex: '#FF0000' },
  { name: 'Green', rgby: '0FF0', hex: '#00FF00' },
  { name: 'Blue', rgby: '00FF', hex: '#0000FF' },
  { name: 'Yellow', rgby: 'BBB1', hex: '#FFFF00' },
  { name: 'Magenta', rgby: 'FC1F', hex: '#FF00FF' },
  { name: 'Cyan', rgby: '0F0F', hex: '#00FFFF' },
  { name: 'Orange', rgby: 'B100', hex: '#FF6600' },
  { name: 'Purple', rgby: 'A50F', hex: '#9900FF' },
  { name: 'White', rgby: 'FFFF', hex: '#FFFFFF' },
  { name: 'Black', rgby: '0010', hex: '#000000' }
]

function ColorPicker({ label, description, value, onChange }) {
  const hexValue = rgbyToHex(value)

  const handleHexChange = (e) => {
    const hex = e.target.value
    const rgby = hexToRgby(hex)
    onChange(rgby)
  }

  const handlePresetClick = (preset) => {
    onChange(preset.rgby)
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
            <span className="laser-color-rgby">RGBY: {formatRgby(value)}</span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.map((preset) => (
            <button
              key={preset.name}
              className={`laser-preset ${value === preset.rgby ? 'active' : ''}`}
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

export default function LaserEditorModal({
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
    wide: 'FC00',
    thin: 'FC00',
    outline: 'FC00'
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod if provided
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          wide: editingMod.modifications.wide?.color || 'FC00',
          thin: editingMod.modifications.thin?.color || 'FC00',
          outline: editingMod.modifications.outline?.color || 'FC00'
        })
      }
    } else {
      // Reset for new mod
      setName('')
      setColors({ wide: 'FC00', thin: 'FC00', outline: 'FC00' })
    }
    setError(null)
  }, [editingMod, show])

  if (!show) return null

  const handleColorChange = (layer, rgby) => {
    setColors(prev => ({ ...prev, [layer]: rgby }))
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
          wide: { color: colors.wide },
          thin: { color: colors.thin },
          outline: { color: colors.outline }
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
      console.error('[LaserEditorModal] Save error:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleApplyToAll = (rgby) => {
    setColors({
      wide: rgby,
      thin: rgby,
      outline: rgby
    })
  }

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Laser Mod' : 'Create Laser Mod'}
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
              placeholder="e.g., Red Laser, Blue Fire..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview */}
          <div className="laser-preview">
            <div className="laser-preview-label">Preview</div>
            <div className="laser-preview-display">
              <div
                className="laser-preview-layer laser-preview-wide"
                style={{ backgroundColor: rgbyToHex(colors.wide), opacity: 0.4 }}
              />
              <div
                className="laser-preview-layer laser-preview-thin"
                style={{ backgroundColor: rgbyToHex(colors.thin), opacity: 0.6 }}
              />
              <div
                className="laser-preview-layer laser-preview-outline"
                style={{ backgroundColor: rgbyToHex(colors.outline) }}
              />
            </div>
          </div>

          {/* Color pickers for each layer */}
          {extraType.properties.map((prop) => (
            <ColorPicker
              key={prop.id}
              label={prop.name}
              description={prop.description}
              value={colors[prop.id]}
              onChange={(rgby) => handleColorChange(prop.id, rgby)}
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
                  onClick={() => handleApplyToAll(preset.rgby)}
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
