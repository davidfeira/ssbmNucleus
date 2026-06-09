import { useState } from 'react'
import { playSound, playHoverSound } from '../../../utils/sounds'
import { ICONS, EffectIcon, PlusIcon, ImportIcon } from './ExtrasIcons'
import { ExtraPreview } from './ExtraPreviews'

/**
 * ExtraTypeCard - Card for selecting an extra type category
 */
export function ExtraTypeCard({ extraType, modCount, onClick }) {
  const Icon = ICONS[extraType.icon] || EffectIcon

  // Build shared text based on sharedWith array
  const getSharedText = () => {
    if (!extraType.shared || !extraType.sharedWith) return null
    const chars = [extraType.owner, ...extraType.sharedWith].filter(Boolean)
    if (chars.length === 2) {
      return `Applies to both ${chars[0]} and ${chars[1]}`
    }
    return `Shared with ${extraType.sharedWith.join(', ')}`
  }

  return (
    <div className="extra-type-page-card" onMouseEnter={playHoverSound} onClick={onClick}>
      <div className="extra-type-page-icon">
        <Icon />
      </div>
      <div className="extra-type-page-info">
        <span className="extra-type-page-name">{extraType.name}</span>
        <span className="extra-type-page-count">
          {modCount} mod{modCount !== 1 ? 's' : ''}
        </span>
        {extraType.shared && (
          <span className="extra-type-shared">{getSharedText()}</span>
        )}
      </div>
    </div>
  )
}

/**
 * ExtraModCard - Individual extra mod card (same size as skin cards)
 */
export function ExtraModCard({ mod, character, extraType, onEdit, onDelete, API_URL }) {
  const isModelType = extraType.type === 'model'

  return (
    <div className="extra-mod-card" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); onEdit?.(mod); }}>
      <div className="extra-mod-image-container">
        {/* Preview based on extra type */}
        <ExtraPreview extraType={extraType} modifications={mod.modifications} mod={mod} compact />
      </div>

      <div className="extra-mod-info">
        <div className="extra-mod-name">{mod.name}</div>
        {mod.source === 'imported' && (
          <div className="extra-mod-badge">Imported</div>
        )}
        {mod.source === 'uploaded' && (
          <div className="extra-mod-badge">Uploaded</div>
        )}
      </div>
    </div>
  )
}

/**
 * CreateExtraModCard - "Create New Mod" card matching skin card size
 * For model types, directly shows import option without create
 */
export function CreateExtraModCard({ extraType, onCreateNew, onImport, uploading }) {
  const [showOptions, setShowOptions] = useState(false)
  const isModelType = extraType?.type === 'model'

  // For model types, clicking directly opens the import modal
  if (isModelType) {
    return (
      <div className="extra-mod-card create-extra-mod-card" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); onCreateNew?.(); }}>
        <div className="extra-mod-image-container create-extra-mod-placeholder">
          <div className="create-extra-mod-icon">
            {uploading ? <span className="create-extra-spinner" /> : <ImportIcon />}
          </div>
        </div>
        <div className="extra-mod-info">
          <div className="extra-mod-name">{uploading ? 'Importing...' : 'Import Model'}</div>
          <div className="extra-mod-hint">.dae or .dat</div>
        </div>
      </div>
    )
  }

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
          <button className="create-extra-mod-cancel" onClick={() => { playSound('back'); setShowOptions(false); }}>
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="extra-mod-card create-extra-mod-card" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); setShowOptions(true); }}>
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
