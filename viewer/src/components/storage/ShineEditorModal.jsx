import { useState, useEffect } from 'react'
import { hexToRgby, rgbyToHex, formatRgby } from '../../utils/rgbyColor'

/**
 * ShineEditorModal - Color picker UI for creating/editing Shine (reflector) mods
 * Supports multiple color properties: hex, inner, outer (RGBY), bubble (42_48)
 * Shared between Fox and Falco
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

// Color presets with both RGBY and RGB values
const COLOR_PRESETS = [
  { name: 'Blue', rgby: '621F', rgb: '0066FF', hex: '#0066FF' },
  { name: 'Red', rgby: 'FC00', rgb: 'FF0000', hex: '#FF0000' },
  { name: 'Green', rgby: '0FF0', rgb: '00FF00', hex: '#00FF00' },
  { name: 'Yellow', rgby: 'BBB1', rgb: 'FFFF00', hex: '#FFFF00' },
  { name: 'Magenta', rgby: 'FC1F', rgb: 'FF00FF', hex: '#FF00FF' },
  { name: 'Cyan', rgby: '0F0F', rgb: '00FFFF', hex: '#00FFFF' },
  { name: 'Purple', rgby: 'A50F', rgb: '9900FF', hex: '#9900FF' },
  { name: 'Orange', rgby: 'FE60', rgb: 'FF6600', hex: '#FF6600' },
  { name: 'White', rgby: 'FFFF', rgb: 'FFFFFF', hex: '#FFFFFF' },
  { name: 'Pink', rgby: 'FB5F', rgb: 'FF66CC', hex: '#FF66CC' }
]

// Default colors matching vanilla
const DEFAULT_COLORS = {
  hex: '621F',      // Blue-ish (RGBY)
  inner: '63FF',    // Blue (RGBY)
  outer: '63FF',    // Blue (RGBY)
  bubble: '808080FFFFFFFFFFFFFFFFFF'  // Gray/white gradient (3x RGBA)
}

// Generate bubble 42_48 data from a tint color
// Format: [tint RGBA] [white RGBA] [white RGBA]
function generateBubbleData(tintHex) {
  // Parse tint color
  const r = parseInt(tintHex.slice(1, 3), 16)
  const g = parseInt(tintHex.slice(3, 5), 16)
  const b = parseInt(tintHex.slice(5, 7), 16)

  // First color: tint with 50% opacity (more visible)
  const c1 = `${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}FF`
  // Second and third: white with full alpha
  const c2 = 'FFFFFFFF'
  const c3 = 'FFFFFFFF'

  return (c1 + c2 + c3).toUpperCase()
}

// Extract tint from bubble data
function extractBubbleTint(bubbleHex) {
  if (!bubbleHex || bubbleHex.length < 6) return '#808080'
  // First 6 chars are RGB of the tint
  return `#${bubbleHex.slice(0, 6)}`
}

// Color picker that supports RGBY format
function ColorPicker({ label, description, value, onChange }) {
  const safeValue = value || '621F'
  const hexValue = rgbyToHex(safeValue)

  const handleHexChange = (e) => {
    const hex = e.target.value
    onChange(hexToRgby(hex))
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
            <span className="laser-color-rgby">RGBY: {formatRgby(safeValue)}</span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.map((preset) => (
            <button
              key={preset.name}
              className={`laser-preset ${safeValue === preset.rgby ? 'active' : ''}`}
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

// Simple RGB color picker for bubble tint
function BubblePicker({ label, description, value, onChange }) {
  const tintHex = extractBubbleTint(value)

  const handleHexChange = (e) => {
    const hex = e.target.value
    onChange(generateBubbleData(hex))
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
            value={tintHex}
            onChange={handleHexChange}
            className="laser-color-input"
          />
          <div className="laser-color-values">
            <span className="laser-color-hex">{tintHex.toUpperCase()}</span>
            <span className="laser-color-rgby">Bubble Tint</span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.slice(0, 6).map((preset) => (
            <button
              key={preset.name}
              className="laser-preset"
              style={{ backgroundColor: preset.hex }}
              onClick={() => onChange(generateBubbleData(preset.hex))}
              title={preset.name}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function ShineEditorModal({
  show,
  character,
  extraType,
  editingMod,
  onClose,
  onSave,
  API_URL
}) {
  const [name, setName] = useState('')
  const [colors, setColors] = useState({ ...DEFAULT_COLORS })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod if provided
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          hex: editingMod.modifications.hex?.color || DEFAULT_COLORS.hex,
          inner: editingMod.modifications.inner?.color || DEFAULT_COLORS.inner,
          outer: editingMod.modifications.outer?.color || DEFAULT_COLORS.outer,
          bubble: editingMod.modifications.bubble?.color || DEFAULT_COLORS.bubble
        })
      }
    } else {
      // Reset for new mod
      setName('')
      setColors({ ...DEFAULT_COLORS })
    }
    setError(null)
  }, [editingMod, show])

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
          hex: { color: colors.hex },
          inner: { color: colors.inner },
          outer: { color: colors.outer },
          bubble: { color: colors.bubble }
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
      console.error('[ShineEditorModal] Save error:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  // Apply preset to all RGBY layers
  const handleApplyToAll = (preset) => {
    setColors(prev => ({
      ...prev,
      hex: preset.rgby,
      inner: preset.rgby,
      outer: preset.rgby
    }))
  }

  // Get display colors for preview
  const hexColor = rgbyToHex(colors.hex)
  const innerColor = rgbyToHex(colors.inner)
  const outerColor = rgbyToHex(colors.outer)
  const bubbleTint = extractBubbleTint(colors.bubble)

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Shine Mod' : 'Create Shine Mod'}
            </span>
            <span className="laser-editor-title-char">{character}</span>
          </div>
          <button className="laser-editor-close" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="laser-editor-body">
          {/* Shared effect note */}
          <div className="shared-note">
            This mod applies to both Fox and Falco
          </div>

          {/* Name input */}
          <div className="laser-editor-name-group">
            <label className="laser-editor-name-label">Mod Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Red Shine, Purple Reflector..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview - hexagon visualization */}
          <div className="laser-preview">
            <div className="laser-preview-label">Preview</div>
            <div className="laser-preview-display" style={{ background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)' }}>
              <div className="shine-preview-container">
                {/* Outer glow */}
                <div
                  style={{
                    position: 'absolute',
                    width: '70px',
                    height: '70px',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: `radial-gradient(ellipse at center, ${outerColor}60 0%, transparent 70%)`,
                    filter: `drop-shadow(0 0 15px ${outerColor}80)`
                  }}
                />
                {/* Inner glow */}
                <div
                  style={{
                    position: 'absolute',
                    width: '50px',
                    height: '50px',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: `radial-gradient(ellipse at center, ${innerColor}80 0%, transparent 60%)`,
                  }}
                />
                {/* Hexagon shape */}
                <div
                  style={{
                    position: 'absolute',
                    width: '40px',
                    height: '40px',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: hexColor,
                    clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                    opacity: 0.9,
                    boxShadow: `0 0 10px ${hexColor}`
                  }}
                />
                {/* Bubble overlay */}
                <div
                  style={{
                    position: 'absolute',
                    width: '55px',
                    height: '55px',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    borderRadius: '50%',
                    border: `2px solid ${bubbleTint}40`,
                    background: `radial-gradient(ellipse at 30% 30%, ${bubbleTint}20 0%, transparent 50%)`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Color pickers */}
          <ColorPicker
            label="Hexagon"
            description="Main shield shape"
            value={colors.hex}
            onChange={(value) => handleColorChange('hex', value)}
          />

          <ColorPicker
            label="Inner Glow"
            description="Inner glow effect"
            value={colors.inner}
            onChange={(value) => handleColorChange('inner', value)}
          />

          <ColorPicker
            label="Outer Glow"
            description="Outer flash effect"
            value={colors.outer}
            onChange={(value) => handleColorChange('outer', value)}
          />

          <BubblePicker
            label="Bubble"
            description="Transparent bubble overlay tint"
            value={colors.bubble}
            onChange={(value) => handleColorChange('bubble', value)}
          />

          {/* Quick apply to all */}
          <div className="laser-apply-all">
            <span className="laser-apply-all-label">Apply to all:</span>
            <div className="laser-apply-all-presets">
              {COLOR_PRESETS.slice(0, 6).map((preset) => (
                <button
                  key={preset.name}
                  className="laser-apply-preset"
                  style={{ backgroundColor: preset.hex }}
                  onClick={() => handleApplyToAll(preset)}
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
