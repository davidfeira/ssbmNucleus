import { useState, useEffect } from 'react'
import { hexToRgby, rgbyToHex, formatRgby } from '../../utils/rgbyColor'

/**
 * UpBEditorModal - Color picker UI for creating/editing Firefox/Firebird flame mods
 * Supports multiple color properties: tip (RGBY), body, trail, rings (RGB)
 * Plus fire texture hue (extracted and hue-shifted)
 * Shared between Fox and Falco
 */

// Convert hue (0-360) to hex color for preview
function hueToHex(hue) {
  // HSL to RGB conversion with full saturation and 50% lightness
  const h = hue / 360
  const s = 1
  const l = 0.5

  const hue2rgb = (p, q, t) => {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1/6) return p + (q - p) * 6 * t
    if (t < 1/2) return q
    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
    return p
  }

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q
  const r = Math.round(hue2rgb(p, q, h + 1/3) * 255)
  const g = Math.round(hue2rgb(p, q, h) * 255)
  const b = Math.round(hue2rgb(p, q, h - 1/3) * 255)

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

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
  { name: 'Fire', rgby: 'FE60', rgb: 'FF6600', hex: '#FF6600' },
  { name: 'Red', rgby: 'FC00', rgb: 'FF0000', hex: '#FF0000' },
  { name: 'Blue', rgby: '00FF', rgb: '0000FF', hex: '#0000FF' },
  { name: 'Green', rgby: '0FF0', rgb: '00FF00', hex: '#00FF00' },
  { name: 'Yellow', rgby: 'BBB1', rgb: 'FFFF00', hex: '#FFFF00' },
  { name: 'Magenta', rgby: 'FC1F', rgb: 'FF00FF', hex: '#FF00FF' },
  { name: 'Cyan', rgby: '0F0F', rgb: '00FFFF', hex: '#00FFFF' },
  { name: 'Purple', rgby: 'A50F', rgb: '9900FF', hex: '#9900FF' },
  { name: 'White', rgby: 'FFFF', rgb: 'FFFFFF', hex: '#FFFFFF' },
  { name: 'Pink', rgby: 'FB5F', rgb: 'FF66CC', hex: '#FF66CC' }
]

// Default colors matching vanilla
const DEFAULT_COLORS = {
  tip: 'FE60',      // Fire orange (RGBY)
  body: 'FFFFFF',   // White (RGB)
  trail: 'FFFFFF',  // White (RGB)
  rings: 'FFFF00'   // Yellow (RGB)
}

// Convert RGB hex to display hex
function rgbToDisplayHex(rgb) {
  if (!rgb || rgb.length < 6) return '#FFFFFF'
  return `#${rgb.substring(0, 6)}`
}

// Convert display hex to RGB
function displayHexToRgb(hex) {
  return hex.replace('#', '').toUpperCase()
}

// Color picker that supports both RGBY and RGB formats
function ColorPicker({ label, description, value, onChange, format = 'RGBY' }) {
  const isRgby = format === 'RGBY'
  const safeValue = value || (isRgby ? 'FE60' : 'FFFFFF')
  const hexValue = isRgby ? rgbyToHex(safeValue) : rgbToDisplayHex(safeValue)

  const handleHexChange = (e) => {
    const hex = e.target.value
    if (isRgby) {
      onChange(hexToRgby(hex))
    } else {
      onChange(displayHexToRgb(hex))
    }
  }

  const handlePresetClick = (preset) => {
    onChange(isRgby ? preset.rgby : preset.rgb)
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
            <span className="laser-color-rgby">
              {isRgby ? `RGBY: ${formatRgby(safeValue)}` : `RGB: ${safeValue}`}
            </span>
          </div>
        </div>

        <div className="laser-color-presets">
          {COLOR_PRESETS.map((preset) => {
            const presetValue = isRgby ? preset.rgby : preset.rgb
            return (
              <button
                key={preset.name}
                className={`laser-preset ${safeValue === presetValue ? 'active' : ''}`}
                style={{ backgroundColor: preset.hex }}
                onClick={() => handlePresetClick(preset)}
                title={preset.name}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}

// Hue picker for texture-based color control
function HuePicker({ label, description, value, onChange, loading }) {
  const hue = value ?? 15 // Default to vanilla fire orange-red
  const previewColor = hueToHex(hue)

  // Hue presets
  const HUE_PRESETS = [
    { name: 'Fire', hue: 15 },
    { name: 'Red', hue: 0 },
    { name: 'Orange', hue: 30 },
    { name: 'Yellow', hue: 60 },
    { name: 'Green', hue: 120 },
    { name: 'Cyan', hue: 180 },
    { name: 'Blue', hue: 240 },
    { name: 'Purple', hue: 280 },
    { name: 'Magenta', hue: 320 }
  ]

  return (
    <div className="laser-color-picker">
      <div className="laser-color-header">
        <span className="laser-color-label">{label}</span>
        <span className="laser-color-description">{description}</span>
      </div>

      <div className="laser-color-controls">
        <div className="laser-color-input-group">
          {/* Color preview swatch */}
          <div
            className="laser-color-input"
            style={{
              backgroundColor: previewColor,
              cursor: 'default'
            }}
          />
          <div className="laser-color-values">
            {loading ? (
              <span className="laser-color-hex">Loading...</span>
            ) : (
              <>
                <span className="laser-color-hex">{previewColor.toUpperCase()}</span>
                <span className="laser-color-rgby">Hue: {Math.round(hue)}°</span>
              </>
            )}
          </div>
        </div>

        {/* Hue slider */}
        <div style={{ width: '100%', marginTop: '8px' }}>
          <input
            type="range"
            min="0"
            max="360"
            value={hue}
            onChange={(e) => onChange(parseInt(e.target.value))}
            disabled={loading}
            style={{
              width: '100%',
              height: '20px',
              cursor: loading ? 'wait' : 'pointer',
              background: 'linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000)',
              borderRadius: '4px',
              WebkitAppearance: 'none',
              appearance: 'none'
            }}
          />
        </div>

        {/* Hue presets */}
        <div className="laser-color-presets" style={{ marginTop: '8px' }}>
          {HUE_PRESETS.map((preset) => (
            <button
              key={preset.name}
              className={`laser-preset ${Math.abs(hue - preset.hue) < 10 ? 'active' : ''}`}
              style={{ backgroundColor: hueToHex(preset.hue) }}
              onClick={() => onChange(preset.hue)}
              title={preset.name}
              disabled={loading}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function UpBEditorModal({
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
  const [textureHue, setTextureHue] = useState(15) // Fire texture hue (vanilla is ~15)
  const [loadingTexture, setLoadingTexture] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod if provided
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          tip: editingMod.modifications.tip?.color || DEFAULT_COLORS.tip,
          body: editingMod.modifications.body?.color || DEFAULT_COLORS.body,
          trail: editingMod.modifications.trail?.color || DEFAULT_COLORS.trail,
          rings: editingMod.modifications.rings?.color || DEFAULT_COLORS.rings
        })
        // Load texture hue from mod if saved
        if (editingMod.modifications.fire?.hue !== undefined) {
          setTextureHue(editingMod.modifications.fire.hue)
        }
      }
    } else {
      // Reset for new mod
      setName('')
      setColors({ ...DEFAULT_COLORS })
    }
    setError(null)
  }, [editingMod, show])

  // Fetch current texture hue when modal opens (lazy load)
  useEffect(() => {
    if (!show) return

    const fetchTextureHue = async () => {
      // Skip if editing a mod that already has the hue saved
      if (editingMod?.modifications?.fire?.hue !== undefined) return

      setLoadingTexture(true)
      try {
        const response = await fetch(`${API_URL}/storage/textures/current/Fox/upb_texture`)
        const data = await response.json()
        if (data.success && data.hue !== null) {
          setTextureHue(data.hue)
        }
      } catch (err) {
        console.warn('[UpBEditorModal] Failed to fetch texture hue:', err)
        // Keep default, don't show error
      } finally {
        setLoadingTexture(false)
      }
    }

    fetchTextureHue()
  }, [show, API_URL, editingMod])

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
          tip: { color: colors.tip },
          body: { color: colors.body },
          trail: { color: colors.trail },
          rings: { color: colors.rings },
          fire: { hue: textureHue } // Store texture hue in mod
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
      console.error('[UpBEditorModal] Save error:', err)
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

  // Apply preset to all layers
  const handleApplyToAll = (preset) => {
    setColors({
      tip: preset.rgby,
      body: preset.rgb,
      trail: preset.rgb,
      rings: preset.rgb
    })
  }

  // Get display colors for preview
  const tipHex = rgbyToHex(colors.tip)
  const bodyHex = rgbToDisplayHex(colors.body)
  const trailHex = rgbToDisplayHex(colors.trail)
  const ringsHex = rgbToDisplayHex(colors.rings)
  const fireHex = hueToHex(textureHue) // Fire texture preview color

  // Get format for each property
  const getFormat = (propId) => {
    const prop = extraType.properties?.find(p => p.id === propId)
    return prop?.format || 'RGBY'
  }

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal">
        <div className="laser-editor-header">
          <div className="laser-editor-title">
            <span className="laser-editor-title-text">
              {editingMod ? 'Edit Up-B Mod' : 'Create Up-B Mod'}
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
              placeholder="e.g., Blue Fire, Purple Flames..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Preview - flame visualization */}
          <div className="laser-preview">
            <div className="laser-preview-label">Preview</div>
            <div className="laser-preview-display" style={{ background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)' }}>
              <div className="upb-preview-container">
                {/* Fire rings (background) */}
                <div
                  className="upb-ring"
                  style={{
                    position: 'absolute',
                    width: '60px',
                    height: '20px',
                    bottom: '15px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    borderRadius: '50%',
                    border: `2px solid ${ringsHex}`,
                    boxShadow: `0 0 8px ${ringsHex}, inset 0 0 4px ${ringsHex}40`,
                    opacity: 0.7
                  }}
                />
                {/* Body glow */}
                <div
                  style={{
                    position: 'absolute',
                    width: '30px',
                    height: '50px',
                    bottom: '10px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: `radial-gradient(ellipse at center, ${bodyHex}40 0%, transparent 70%)`,
                    filter: `drop-shadow(0 0 10px ${bodyHex}60)`
                  }}
                />
                {/* Trail particles */}
                {[0.2, 0.4, 0.6].map((opacity, i) => (
                  <div
                    key={i}
                    style={{
                      position: 'absolute',
                      width: '8px',
                      height: '8px',
                      bottom: `${25 + i * 12}px`,
                      left: `${42 + (i % 2 ? 5 : -5)}%`,
                      borderRadius: '50%',
                      background: trailHex,
                      opacity: opacity,
                      boxShadow: `0 0 4px ${trailHex}`
                    }}
                  />
                ))}
                {/* Main flame tip */}
                <div
                  style={{
                    position: 'absolute',
                    width: '24px',
                    height: '36px',
                    bottom: '5px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    background: `linear-gradient(to top, ${tipHex} 0%, ${tipHex}CC 40%, ${tipHex}66 70%, transparent 100%)`,
                    filter: `drop-shadow(0 0 6px ${tipHex})`
                  }}
                />
                {/* Inner core */}
                <div
                  style={{
                    position: 'absolute',
                    width: '10px',
                    height: '18px',
                    bottom: '8px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    background: `linear-gradient(to top, #FFFFFF 0%, ${tipHex} 60%, transparent 100%)`
                  }}
                />
              </div>
            </div>
          </div>

          {/* Color pickers for each property */}
          {extraType.properties?.map((prop) => (
            <ColorPicker
              key={prop.id}
              label={prop.name}
              description={prop.description}
              value={colors[prop.id]}
              onChange={(value) => handleColorChange(prop.id, value)}
              format={prop.format || 'RGBY'}
            />
          ))}

          {/* Fire texture hue picker */}
          <HuePicker
            label="Fire Texture"
            description="Main fire/flame texture color"
            value={textureHue}
            onChange={setTextureHue}
            loading={loadingTexture}
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
