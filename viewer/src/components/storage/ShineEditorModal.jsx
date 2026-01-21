import { useState, useEffect } from 'react'
import { hexToRgby, rgbyToHex, formatRgby } from '../../utils/rgbyColor'

/**
 * ShineEditorModal - Two-color gradient editor for Fox/Falco shine
 *
 * The shine has a two-color gradient pattern:
 * - Primary (621F vanilla) - bright edge/outline vertices
 * - Secondary (AB9F vanilla) - fill/interior vertices
 *
 * Working mods replace these in pairs (e.g., Green: 621F→0FF0, AB9F→0A45)
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

/**
 * Interactive SVG Hexagon showing the two-color gradient
 * Primary = edge/outline, Secondary = fill
 */
function ShineHexagonSVG({ primaryColor, secondaryColor, selectedLayer, onLayerClick }) {
  // Outer hexagon points
  const outerHex = [
    { x: 100, y: 20 },
    { x: 165, y: 52 },
    { x: 165, y: 128 },
    { x: 100, y: 160 },
    { x: 35, y: 128 },
    { x: 35, y: 52 }
  ]

  // Inner hexagon (fill area)
  const innerHex = [
    { x: 100, y: 55 },
    { x: 135, y: 75 },
    { x: 135, y: 115 },
    { x: 100, y: 135 },
    { x: 65, y: 115 },
    { x: 65, y: 75 }
  ]

  const toPointsStr = (pts) => pts.map(p => `${p.x},${p.y}`).join(' ')
  const isSelected = (layer) => selectedLayer === layer

  return (
    <svg viewBox="0 0 200 180" className="shine-hexagon-svg" style={{ width: '100%', maxWidth: '220px' }}>
      <defs>
        <filter id="shineGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        <filter id="shineGlowStrong" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        {/* Gradient showing primary->secondary transition */}
        <radialGradient id="fillGradient" cx="50%" cy="50%" r="70%">
          <stop offset="0%" stopColor={secondaryColor} stopOpacity="0.9" />
          <stop offset="60%" stopColor={secondaryColor} stopOpacity="0.7" />
          <stop offset="100%" stopColor={primaryColor} stopOpacity="0.5" />
        </radialGradient>
      </defs>

      {/* Background */}
      <rect x="0" y="0" width="200" height="180" fill="#0a0a12" rx="8" />

      {/* Outer glow aura using primary */}
      <polygon
        points={toPointsStr(outerHex)}
        fill={primaryColor}
        fillOpacity="0.15"
        filter="url(#shineGlowStrong)"
      />

      {/* Fill area - SECONDARY color (clickable) */}
      <g onClick={() => onLayerClick('secondary')} style={{ cursor: 'pointer' }}>
        <polygon
          points={toPointsStr(outerHex)}
          fill="url(#fillGradient)"
          stroke="none"
        />
        <polygon
          points={toPointsStr(innerHex)}
          fill={secondaryColor}
          fillOpacity={isSelected('secondary') ? 0.9 : 0.75}
          filter="url(#shineGlow)"
        />
        {isSelected('secondary') && (
          <polygon
            points={toPointsStr(innerHex)}
            fill="none"
            stroke="#fff"
            strokeWidth="2"
            strokeDasharray="4,4"
          />
        )}
      </g>

      {/* Edge/outline - PRIMARY color (clickable) */}
      <g onClick={() => onLayerClick('primary')} style={{ cursor: 'pointer' }}>
        {/* Outer edge stroke */}
        <polygon
          points={toPointsStr(outerHex)}
          fill="none"
          stroke={primaryColor}
          strokeWidth={isSelected('primary') ? 6 : 4}
          filter="url(#shineGlow)"
        />
        {/* Inner edge stroke */}
        <polygon
          points={toPointsStr(innerHex)}
          fill="none"
          stroke={primaryColor}
          strokeWidth={isSelected('primary') ? 4 : 2}
          strokeOpacity="0.8"
        />
        {/* Vertex dots */}
        {outerHex.map((p, i) => (
          <circle
            key={`v-${i}`}
            cx={p.x} cy={p.y}
            r={isSelected('primary') ? 6 : 4}
            fill={primaryColor}
            filter="url(#shineGlow)"
          />
        ))}
        {isSelected('primary') && (
          <polygon
            points={toPointsStr(outerHex)}
            fill="none"
            stroke="#fff"
            strokeWidth="2"
            strokeDasharray="6,3"
          />
        )}
      </g>

      {/* Labels */}
      <g fill="#666" fontSize="10" fontFamily="sans-serif" fontWeight="bold" style={{ pointerEvents: 'none' }}>
        <text x="100" y="98" textAnchor="middle" fill={isSelected('secondary') ? '#fff' : '#888'}>FILL</text>
        <text x="100" y="38" textAnchor="middle" fill={isSelected('primary') ? '#fff' : '#888'}>EDGE</text>
      </g>
    </svg>
  )
}

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

// Preset shine color combinations (matching known working mods)
const SHINE_PRESETS = [
  { name: 'Vanilla Blue', primary: '621F', secondary: 'AB9F' },
  { name: 'Green', primary: '0FF0', secondary: '0A45' },
  { name: 'Purple', primary: 'FCCC', secondary: 'A50F' },
  { name: 'Red', primary: 'FC00', secondary: '8800' },
  { name: 'White', primary: 'FFFF', secondary: 'AAAA' },
  { name: 'Gray', primary: 'FFFF', secondary: '5D88' }
]

// Default colors matching vanilla shine
const DEFAULT_COLORS = {
  primary: '621F',    // Vanilla bright blue edge
  secondary: 'AB9F'   // Vanilla grayish fill
}

// Layer metadata for UI
const LAYER_INFO = {
  primary: { label: 'Primary (Edge)', desc: 'Bright edge/outline color' },
  secondary: { label: 'Secondary (Fill)', desc: 'Fill/interior color' }
}

// RGBY Color picker component
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

export default function ShineEditorModal({
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
  const [selectedLayer, setSelectedLayer] = useState('primary')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

  // Initialize from editing mod if provided
  useEffect(() => {
    if (editingMod) {
      setName(editingMod.name || '')
      if (editingMod.modifications) {
        setColors({
          primary: editingMod.modifications.primary?.color || DEFAULT_COLORS.primary,
          secondary: editingMod.modifications.secondary?.color || DEFAULT_COLORS.secondary
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
          primary: { color: colors.primary },
          secondary: { color: colors.secondary }
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

  // Apply a preset combination
  const handleApplyPreset = (preset) => {
    setColors({
      primary: preset.primary,
      secondary: preset.secondary
    })
  }

  // Get display colors for SVG preview
  const primaryHex = rgbyToHex(colors.primary)
  const secondaryHex = rgbyToHex(colors.secondary)

  // Get current layer info
  const currentLayerInfo = LAYER_INFO[selectedLayer]

  return (
    <div className="laser-editor-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="laser-editor-modal shine-editor-modal">
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
            Shared between Fox and Falco
          </div>

          {/* Name input */}
          <div className="laser-editor-name-group">
            <label className="laser-editor-name-label">Mod Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Green Shine, Purple Reflector..."
              className="laser-editor-name-input"
            />
          </div>

          {/* Interactive SVG Hexagon - click to select layer */}
          <div className="shine-interactive-preview">
            <div className="shine-preview-label">Click a region to edit its color</div>
            <div className="shine-svg-container">
              <ShineHexagonSVG
                primaryColor={primaryHex}
                secondaryColor={secondaryHex}
                selectedLayer={selectedLayer}
                onLayerClick={setSelectedLayer}
              />
              <div className="shine-layer-indicator">
                <span className="shine-layer-name" style={{ color: selectedLayer === 'primary' ? primaryHex : secondaryHex }}>
                  {currentLayerInfo?.label}: {currentLayerInfo?.desc}
                </span>
              </div>
            </div>
          </div>

          {/* Layer selector buttons */}
          <div className="shine-layer-buttons">
            <button
              className={`shine-layer-btn ${selectedLayer === 'primary' ? 'selected' : ''}`}
              style={{
                '--layer-color': primaryHex,
                borderColor: selectedLayer === 'primary' ? primaryHex : undefined
              }}
              onClick={() => setSelectedLayer('primary')}
            >
              <span className="shine-layer-btn-dot" style={{ backgroundColor: primaryHex }} />
              <span className="shine-layer-btn-label">Edge</span>
            </button>
            <button
              className={`shine-layer-btn ${selectedLayer === 'secondary' ? 'selected' : ''}`}
              style={{
                '--layer-color': secondaryHex,
                borderColor: selectedLayer === 'secondary' ? secondaryHex : undefined
              }}
              onClick={() => setSelectedLayer('secondary')}
            >
              <span className="shine-layer-btn-dot" style={{ backgroundColor: secondaryHex }} />
              <span className="shine-layer-btn-label">Fill</span>
            </button>
          </div>

          {/* Color picker for selected layer */}
          <div className="shine-active-picker">
            <ColorPicker
              label={currentLayerInfo?.label}
              description={currentLayerInfo?.desc}
              value={colors[selectedLayer]}
              onChange={(value) => handleColorChange(selectedLayer, value)}
            />
          </div>

          {/* Quick preset combinations */}
          <div className="laser-apply-all">
            <span className="laser-apply-all-label">Presets:</span>
            <div className="laser-apply-all-presets">
              {SHINE_PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  className="laser-apply-preset shine-preset-combo"
                  style={{
                    background: `linear-gradient(135deg, ${rgbyToHex(preset.primary)} 50%, ${rgbyToHex(preset.secondary)} 50%)`
                  }}
                  onClick={() => handleApplyPreset(preset)}
                  title={preset.name}
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
