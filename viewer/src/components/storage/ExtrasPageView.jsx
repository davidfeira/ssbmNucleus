import { getExtraTypes } from '../../config/extraTypes'
import { playSound } from '../../utils/sounds'
import useExtrasManager from './extras/useExtrasManager'
import { ExtraTypeCard, ExtraModCard, CreateExtraModCard } from './extras/ExtraCards'
import ExtraEditorModals from './extras/ExtraEditorModals'

/**
 * ExtrasPageView - Full-page view for managing character extras
 * Follows the same pattern as CharacterDetailView
 */
export default function ExtrasPageView({
  character,
  onBack,
  onRefresh,
  API_URL
}) {
  const {
    selectedType,
    setSelectedType,
    extras,
    loading,
    uploading,
    showEditor,
    editingMod,
    handleCreateNew,
    handleEdit,
    handleDelete,
    handleImport,
    handleEditorClose,
    handleSave
  } = useExtrasManager({ character, API_URL, onRefresh })

  const extraTypes = getExtraTypes(character)

  // Currently viewing mods for a specific type
  if (selectedType) {
    const mods = extras[selectedType.id] || []

    return (
      <div className="storage-viewer">
        <div className="character-detail extras-page">
          <div className="character-header">
            <button onClick={() => { playSound('back'); setSelectedType(null); }} className="back-button">
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
              extraType={selectedType}
              onCreateNew={handleCreateNew}
              onImport={handleImport}
              uploading={uploading}
            />
          </div>
        </div>

        <ExtraEditorModals
          selectedType={selectedType}
          character={character}
          API_URL={API_URL}
          editor={{
            show: showEditor,
            editingMod,
            onClose: handleEditorClose,
            onSave: handleSave,
            onDelete: handleDelete
          }}
        />
      </div>
    )
  }

  // Main extras view - show extra type categories
  return (
    <div className="storage-viewer">
      <div className="character-detail extras-page">
        <div className="character-header">
          <button onClick={() => { playSound('back'); onBack(); }} className="back-button">
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
                onClick={() => { playSound('boop'); setSelectedType(type); }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
