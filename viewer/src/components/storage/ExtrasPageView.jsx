import { useState, useEffect, useCallback } from 'react'
import { getExtraTypes, getExtraType } from '../../config/extraTypes'
import { rgbyToHex } from '../../utils/rgbyColor'
import LaserEditorModal from './LaserEditorModal'
import SideBEditorModal from './SideBEditorModal'
import UpBEditorModal from './UpBEditorModal'
import ShineEditorModal from './ShineEditorModal'

/**
 * ExtrasPageView - Full-page view for managing character extras
 * Follows the same pattern as CharacterDetailView
 */

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
)

const EditIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
  </svg>
)

const PlusIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
)

const ImportIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
)

// Icon for laser extra type
const LaserIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="2" y1="12" x2="22" y2="12" strokeLinecap="round" />
    <circle cx="12" cy="12" r="2" fill="currentColor" />
    <path d="M4 8l2 4-2 4" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M20 8l-2 4 2 4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

// Icon for side-B extra type (afterimage/dash effect)
const SideBIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 12h4M9 12h4M14 12h4" strokeLinecap="round" opacity="0.3" />
    <path d="M18 12h4" strokeLinecap="round" />
    <path d="M20 8l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

// Icon for up-B extra type (Firefox/Firebird flame)
const UpBIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22c-4 0-7-3-7-7 0-2 1-4 2-5 0 2 1 3 2 3 0-3 2-6 3-8 1 2 3 5 3 8 1 0 2-1 2-3 1 1 2 3 2 5 0 4-3 7-7 7z" strokeLinejoin="round" />
    <path d="M12 22v-5" strokeLinecap="round" />
  </svg>
)

// Icon for shine (reflector/down-B)
const ShineIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="12,2 15,9 22,9 17,14 19,22 12,17 5,22 7,14 2,9 9,9" strokeLinejoin="round" />
  </svg>
)

const EffectIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" />
  </svg>
)

const ICONS = { laser: LaserIcon, sideb: SideBIcon, upb: UpBIcon, shine: ShineIcon, effect: EffectIcon }

/**
 * LaserBeamPreview - Reusable laser visualization component
 * Renders layered beam effect matching actual in-game appearance
 */
function LaserBeamPreview({ modifications, compact = false }) {
  // Get colors from modifications, handling both RGBY and RGB formats
  const getColor = (layerId) => {
    const mod = modifications?.[layerId]
    if (!mod?.color) return null
    // Center layer is RGB format, others are RGBY
    if (layerId === 'center') {
      return `#${mod.color}`
    }
    return rgbyToHex(mod.color)
  }

  const wide = getColor('wide') || '#ff0000'
  const thin = getColor('thin') || '#ff0000'
  const outline = getColor('outline') || '#ff0000'
  const center = getColor('center') || '#ffffff'

  const height = compact ? 40 : 50

  return (
    <div
      className="laser-beam-preview"
      style={{
        position: 'relative',
        height: `${height}px`,
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Wide glow */}
      <div
        style={{
          position: 'absolute',
          left: '8%',
          right: '8%',
          height: compact ? '24px' : '30px',
          borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${wide} 5%, ${wide} 95%, transparent 100%)`,
          boxShadow: `0 0 15px ${wide}50, 0 0 30px ${wide}30`,
          opacity: 0.5
        }}
      />
      {/* Thin layer */}
      <div
        style={{
          position: 'absolute',
          left: '8%',
          right: '8%',
          height: compact ? '14px' : '18px',
          borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${thin} 3%, ${thin} 97%, transparent 100%)`,
          boxShadow: `0 0 8px ${thin}70`,
          opacity: 0.7
        }}
      />
      {/* Outline */}
      <div
        style={{
          position: 'absolute',
          left: '8%',
          right: '8%',
          height: compact ? '8px' : '10px',
          borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${outline} 2%, ${outline} 98%, transparent 100%)`,
          boxShadow: `0 0 5px ${outline}90`,
          opacity: 0.9
        }}
      />
      {/* Center */}
      <div
        style={{
          position: 'absolute',
          left: '8%',
          right: '8%',
          height: '3px',
          borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${center} 2%, ${center} 98%, transparent 100%)`,
          boxShadow: `0 0 3px ${center}`
        }}
      />
    </div>
  )
}

/**
 * SideBPreview - Preview component for side-B afterimage colors
 * Shows the three RGBA colors as a gradient dash effect
 */
function SideBPreview({ modifications, compact = false }) {
  // Get colors from modifications (RGBA format as hex string)
  const getColor = (layerId) => {
    const mod = modifications?.[layerId]
    if (!mod?.color) return null
    // RGBA format: first 6 chars are RGB
    const hex = mod.color.substring(0, 6)
    return `#${hex}`
  }

  const primary = getColor('primary') || '#0099FF'
  const secondary = getColor('secondary') || '#CCE6FF'
  const tertiary = getColor('tertiary') || '#FFFFFF'

  const height = compact ? 40 : 50

  return (
    <div
      className="sideb-preview"
      style={{
        position: 'relative',
        height: `${height}px`,
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        padding: '0 8px'
      }}
    >
      {/* Afterimage trail - multiple fading copies */}
      {[0.15, 0.3, 0.5, 0.7].map((opacity, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: `${10 + i * 18}%`,
            width: compact ? '16px' : '20px',
            height: compact ? '24px' : '30px',
            borderRadius: '4px',
            background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
            opacity: opacity,
            boxShadow: `0 0 ${8 + i * 4}px ${primary}40`
          }}
        />
      ))}
      {/* Main character silhouette */}
      <div
        style={{
          position: 'absolute',
          right: '12%',
          width: compact ? '20px' : '24px',
          height: compact ? '28px' : '34px',
          borderRadius: '4px',
          background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
          boxShadow: `0 0 12px ${primary}60, 0 0 20px ${secondary}40`
        }}
      />
    </div>
  )
}

/**
 * UpBPreview - Preview component for up-B flame colors
 * Shows tip, body, trail, and rings colors
 */
function UpBPreview({ modifications, compact = false }) {
  // Get colors from modifications
  const tipColor = modifications?.tip?.color ? rgbyToHex(modifications.tip.color) : '#FF6600'
  const bodyColor = modifications?.body?.color ? `#${modifications.body.color}` : '#FFFFFF'
  const trailColor = modifications?.trail?.color ? `#${modifications.trail.color}` : '#FFFFFF'
  const ringsColor = modifications?.rings?.color ? `#${modifications.rings.color}` : '#FFFF00'

  const height = compact ? 40 : 50

  return (
    <div
      className="upb-preview"
      style={{
        position: 'relative',
        height: `${height}px`,
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Fire ring */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '50px' : '60px',
          height: compact ? '16px' : '20px',
          bottom: compact ? '8px' : '10px',
          borderRadius: '50%',
          border: `2px solid ${ringsColor}`,
          boxShadow: `0 0 6px ${ringsColor}`,
          opacity: 0.6
        }}
      />
      {/* Body glow */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '24px' : '30px',
          height: compact ? '40px' : '50px',
          bottom: compact ? '5px' : '5px',
          background: `radial-gradient(ellipse at center, ${bodyColor}30 0%, transparent 70%)`,
          filter: `drop-shadow(0 0 8px ${bodyColor}40)`
        }}
      />
      {/* Trail particles */}
      {[0.3, 0.5].map((opacity, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: '6px',
            height: '6px',
            bottom: `${compact ? 20 : 25 + i * 10}px`,
            left: `${45 + (i % 2 ? 5 : -5)}%`,
            borderRadius: '50%',
            background: trailColor,
            opacity: opacity,
            boxShadow: `0 0 3px ${trailColor}`
          }}
        />
      ))}
      {/* Main flame */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '18px' : '22px',
          height: compact ? '28px' : '34px',
          bottom: compact ? '2px' : '0',
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          background: `linear-gradient(to top, ${tipColor} 0%, ${tipColor}CC 40%, ${tipColor}66 70%, transparent 100%)`,
          filter: `drop-shadow(0 0 5px ${tipColor})`
        }}
      />
      {/* Inner core */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '8px' : '10px',
          height: compact ? '14px' : '18px',
          bottom: compact ? '4px' : '3px',
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          background: `linear-gradient(to top, #FFFFFF 0%, ${tipColor} 60%, transparent 100%)`
        }}
      />
    </div>
  )
}

function ShinePreview({ modifications, compact = false }) {
  // Get colors from modifications
  const hexColor = modifications?.hex?.color ? rgbyToHex(modifications.hex.color) : '#0066FF'
  const innerColor = modifications?.inner?.color ? rgbyToHex(modifications.inner.color) : '#0066FF'
  const outerColor = modifications?.outer?.color ? rgbyToHex(modifications.outer.color) : '#0066FF'

  // Extract bubble tint from 42_48 data (first 6 hex chars are RGB)
  const bubbleData = modifications?.bubble?.color || '808080FFFFFFFFFFFFFFFFFF'
  const bubbleTint = `#${bubbleData.slice(0, 6)}`

  const size = compact ? 36 : 50

  return (
    <div
      className="shine-preview"
      style={{
        position: 'relative',
        height: `${size}px`,
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* Outer glow */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '45px' : '60px',
          height: compact ? '45px' : '60px',
          background: `radial-gradient(ellipse at center, ${outerColor}50 0%, transparent 70%)`,
          filter: `drop-shadow(0 0 10px ${outerColor}60)`
        }}
      />
      {/* Inner glow */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '35px' : '45px',
          height: compact ? '35px' : '45px',
          background: `radial-gradient(ellipse at center, ${innerColor}70 0%, transparent 60%)`
        }}
      />
      {/* Hexagon */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '26px' : '34px',
          height: compact ? '26px' : '34px',
          background: hexColor,
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          opacity: 0.85,
          boxShadow: `0 0 8px ${hexColor}`
        }}
      />
      {/* Bubble overlay */}
      <div
        style={{
          position: 'absolute',
          width: compact ? '38px' : '48px',
          height: compact ? '38px' : '48px',
          borderRadius: '50%',
          border: `1px solid ${bubbleTint}30`,
          background: `radial-gradient(ellipse at 30% 30%, ${bubbleTint}15 0%, transparent 50%)`
        }}
      />
    </div>
  )
}

/**
 * ExtraPreview - Renders appropriate preview based on extra type
 */
function ExtraPreview({ extraType, modifications, compact = false }) {
  if (extraType.id === 'sideb') {
    return <SideBPreview modifications={modifications} compact={compact} />
  }
  if (extraType.id === 'upb') {
    return <UpBPreview modifications={modifications} compact={compact} />
  }
  if (extraType.id === 'shine') {
    return <ShinePreview modifications={modifications} compact={compact} />
  }
  // Default to laser preview
  return <LaserBeamPreview modifications={modifications} compact={compact} />
}

/**
 * ExtraTypeCard - Card for selecting an extra type category
 */
function ExtraTypeCard({ extraType, modCount, onClick }) {
  const Icon = ICONS[extraType.icon] || EffectIcon

  return (
    <div className="extra-type-page-card" onClick={onClick}>
      <div className="extra-type-page-icon">
        <Icon />
      </div>
      <div className="extra-type-page-info">
        <span className="extra-type-page-name">{extraType.name}</span>
        <span className="extra-type-page-count">
          {modCount} mod{modCount !== 1 ? 's' : ''}
        </span>
        {extraType.shared && (
          <span className="extra-type-shared">Applies to both Fox and Falco</span>
        )}
      </div>
    </div>
  )
}

/**
 * ExtraModCard - Individual extra mod card (same size as skin cards)
 */
function ExtraModCard({ mod, character, extraType, onEdit, onDelete, API_URL }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm(`Delete "${mod.name}"?`)) return

    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/storage/extras/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          extraType: extraType.id,
          modId: mod.id
        })
      })
      const data = await response.json()
      if (data.success) {
        onDelete?.(mod.id)
      } else {
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      console.error('[ExtraModCard] Delete error:', err)
      alert(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="extra-mod-card" onClick={() => onEdit?.(mod)}>
      <div className="extra-mod-image-container">
        {/* Preview based on extra type */}
        <ExtraPreview extraType={extraType} modifications={mod.modifications} compact />

        {/* Edit button */}
        <button
          className="btn-edit"
          onClick={(e) => { e.stopPropagation(); onEdit?.(mod) }}
          title="Edit"
        >
          ✎
        </button>

        {/* Delete button */}
        <button
          className="extra-mod-delete"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete"
        >
          <TrashIcon />
        </button>
      </div>

      <div className="extra-mod-info">
        <div className="extra-mod-name">{mod.name}</div>
        {mod.source === 'imported' && (
          <div className="extra-mod-badge">Imported</div>
        )}
      </div>
    </div>
  )
}

/**
 * CreateExtraModCard - "Create New Mod" card matching skin card size
 */
function CreateExtraModCard({ onCreateNew, onImport, uploading }) {
  const [showOptions, setShowOptions] = useState(false)

  if (showOptions) {
    return (
      <div className="extra-mod-card create-extra-mod-card expanded">
        <div className="create-extra-mod-options">
          <button className="create-extra-mod-option" onClick={() => { setShowOptions(false); onCreateNew?.() }}>
            <PlusIcon />
            <span>Create New</span>
          </button>
          <button className="create-extra-mod-option" onClick={() => { setShowOptions(false); onImport?.() }}>
            <ImportIcon />
            <span>Import .dat</span>
          </button>
          <button className="create-extra-mod-cancel" onClick={() => setShowOptions(false)}>
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="extra-mod-card create-extra-mod-card" onClick={() => setShowOptions(true)}>
      <div className="extra-mod-image-container create-extra-mod-placeholder">
        <div className="create-extra-mod-icon">
          {uploading ? <span className="create-extra-spinner" /> : <PlusIcon />}
        </div>
      </div>
      <div className="extra-mod-info">
        <div className="extra-mod-name">{uploading ? 'Importing...' : 'Create New Mod'}</div>
      </div>
    </div>
  )
}

export default function ExtrasPageView({
  character,
  onBack,
  onRefresh,
  API_URL
}) {
  const [selectedType, setSelectedType] = useState(null)
  const [extras, setExtras] = useState({})
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [editingMod, setEditingMod] = useState(null)
  const [uploading, setUploading] = useState(false)

  const extraTypes = getExtraTypes(character)

  // Fetch extras for this character
  const fetchExtras = useCallback(async () => {
    if (!character) return
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/storage/extras/list/${character}`)
      const data = await response.json()
      if (data.success) {
        setExtras(data.extras || {})
      } else {
        setExtras({})
      }
    } catch (err) {
      console.error('[ExtrasPageView] Fetch error:', err)
      setExtras({})
    } finally {
      setLoading(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    fetchExtras()
  }, [fetchExtras])

  const handleRefresh = () => {
    fetchExtras()
    onRefresh?.()
  }

  const handleCreateNew = () => {
    setEditingMod(null)
    setShowEditor(true)
  }

  const handleEdit = (mod) => {
    setEditingMod(mod)
    setShowEditor(true)
  }

  const handleDelete = () => {
    handleRefresh()
  }

  const handleImport = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.dat'
    input.onchange = async (e) => {
      const file = e.target.files?.[0]
      if (!file) return

      setUploading(true)
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('character', character)
        formData.append('extraType', selectedType.id)

        const response = await fetch(`${API_URL}/storage/extras/import`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()
        if (data.success) {
          handleRefresh()
        } else {
          alert(`Import failed: ${data.error}`)
        }
      } catch (err) {
        console.error('[ExtrasPageView] Import error:', err)
        alert(`Import error: ${err.message}`)
      } finally {
        setUploading(false)
      }
    }
    input.click()
  }

  const handleEditorClose = () => {
    setShowEditor(false)
    setEditingMod(null)
  }

  const handleSave = () => {
    handleRefresh()
  }

  // Currently viewing mods for a specific type
  if (selectedType) {
    const mods = extras[selectedType.id] || []

    return (
      <div className="storage-viewer">
        <div className="character-detail extras-page">
          <div className="character-header">
            <button onClick={() => setSelectedType(null)} className="back-button">
              ← Back to Extras
            </button>
            <div className="character-title-area">
              <h2 className="character-name">{selectedType.name}</h2>
              <span className="character-skin-count">{mods.length} mod{mods.length !== 1 ? 's' : ''}</span>
            </div>
          </div>

          <div className="skins-grid">
            {mods.map(mod => (
              <ExtraModCard
                key={mod.id}
                mod={mod}
                character={character}
                extraType={selectedType}
                onEdit={handleEdit}
                onDelete={handleDelete}
                API_URL={API_URL}
              />
            ))}
            <CreateExtraModCard
              onCreateNew={handleCreateNew}
              onImport={handleImport}
              uploading={uploading}
            />
          </div>
        </div>

        {/* Laser Editor Modal */}
        {selectedType.id === 'laser' && (
          <LaserEditorModal
            show={showEditor}
            character={character}
            extraType={selectedType}
            editingMod={editingMod}
            onClose={handleEditorClose}
            onSave={handleSave}
            API_URL={API_URL}
          />
        )}

        {/* Side-B Editor Modal */}
        {selectedType.id === 'sideb' && (
          <SideBEditorModal
            show={showEditor}
            character={character}
            extraType={selectedType}
            editingMod={editingMod}
            onClose={handleEditorClose}
            onSave={handleSave}
            API_URL={API_URL}
          />
        )}

        {/* Up-B Editor Modal */}
        {selectedType.id === 'upb' && (
          <UpBEditorModal
            show={showEditor}
            character={character}
            extraType={selectedType}
            editingMod={editingMod}
            onClose={handleEditorClose}
            onSave={handleSave}
            API_URL={API_URL}
          />
        )}

        {/* Shine Editor Modal */}
        {selectedType.id === 'shine' && (
          <ShineEditorModal
            show={showEditor}
            character={character}
            extraType={selectedType}
            editingMod={editingMod}
            onClose={handleEditorClose}
            onSave={handleSave}
            API_URL={API_URL}
          />
        )}
      </div>
    )
  }

  // Main extras view - show extra type categories
  return (
    <div className="storage-viewer">
      <div className="character-detail extras-page">
        <div className="character-header">
          <button onClick={onBack} className="back-button">
            ← Back to {character}
          </button>
          <div className="character-title-area">
            <h2 className="character-name">Extras</h2>
            <span className="character-skin-count">{character}</span>
          </div>
        </div>

        {loading ? (
          <div className="extras-page-loading">Loading extras...</div>
        ) : extraTypes.length === 0 ? (
          <div className="extras-page-empty">
            <p>No extras available for {character}.</p>
            <p>Extra types will be added in future updates.</p>
          </div>
        ) : (
          <div className="skins-grid extras-type-grid">
            {extraTypes.map(type => (
              <ExtraTypeCard
                key={type.id}
                extraType={type}
                modCount={(extras[type.id] || []).length}
                onClick={() => setSelectedType(type)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
