/**
 * ExtrasView - the extras-mode UI of CharacterMode
 * (extra type list, current-in-MEX preview, available-to-import list)
 */
import { getExtraTypes } from '../../../config/extraTypes'
import { playSound, playHoverSound } from '../../../utils/sounds'
import HexagonLoader from '../../shared/HexagonLoader'
import PaginationBar from '../../shared/PaginationBar'
import usePagination from '../../shared/usePagination'
import { ExtraPreview, ModelPreview, currentColorsToMods } from './ExtraPreviews'

export default function ExtrasView({ selectedFighter, extras }) {
  const {
    setExtrasMode,
    selectedExtraType,
    setSelectedExtraType,
    extraMods,
    selectedExtraMod,
    setSelectedExtraMod,
    importingExtra,
    currentColors,
    setCurrentColors,
    isVanilla,
    getAllMods,
    handleImportExtra,
    handleRestoreVanilla
  } = extras

  const extraTypes = getExtraTypes(selectedFighter.name)
  const availableMods = selectedExtraType ? getAllMods(selectedExtraType.id) : []
  const modsPager = usePagination(availableMods.length, selectedExtraType?.id)
  console.log('[CharacterMode] Extras for', selectedFighter.name, ':', extraTypes.map(t => t.id))
  if (selectedExtraType) {
    console.log('[CharacterMode] Selected extra type:', selectedExtraType.id, selectedExtraType)
  }

  return (
    <div className="mex-content">
      <div className="fighters-list">
        <div className="extras-header">
          <h3>Extras</h3>
          <button
            className="btn-back-small"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('back'); setExtrasMode(false); setSelectedExtraType(null); setSelectedExtraMod(null); setCurrentColors(null); }}
          >
            ← Back
          </button>
        </div>
        <div className="fighter-items">
          {extraTypes.map(extraType => (
            <div
              key={extraType.id}
              className={`fighter-item ${selectedExtraType?.id === extraType.id ? 'selected' : ''}`}
              onClick={() => setSelectedExtraType(extraType)}
            >
              <div className="fighter-content">
                <div className="fighter-name">{extraType.name}</div>
                <div className="fighter-info">
                  <span className="costume-count">
                    {(extraMods[extraType.id] || []).length} in vault
                  </span>
                  {extraType.shared && extraType.sharedWith && (
                    <span className="shared-note">
                      Applies to {extraType.owner} & {extraType.sharedWith.join(', ')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="costumes-panel">
        {selectedExtraType ? (
          <>
            {/* Currently in MEX section - shows actual colors from .dat (or model status) */}
            <div className="costumes-section">
              <h3>Currently in MEX</h3>
              <div className="costume-list existing">
                {selectedExtraType.type === 'model' ? (
                  // Model type - just show a placeholder, no color preview
                  <div className="costume-card existing-costume">
                    <div className="costume-preview" style={{ padding: '8px' }}>
                      <ModelPreview mod={{ name: 'Current' }} compact />
                    </div>
                    <div className="costume-info">
                      <h4>Current Model</h4>
                      <span style={{ fontSize: '11px', color: '#888' }}>Select a model below to replace</span>
                    </div>
                  </div>
                ) : (
                  // Color type - show current colors
                  <div className={`costume-card existing-costume ${isVanilla ? 'vanilla-extra' : ''}`}>
                    <div className="costume-preview" style={{ padding: '8px' }}>
                      {currentColors ? (
                        <ExtraPreview extraType={selectedExtraType} modifications={currentColorsToMods(currentColors)} compact />
                      ) : (
                        <div className="vanilla-preview"><span>Loading...</span></div>
                      )}
                      {!isVanilla && (
                        <button
                          className="btn-remove"
                          onClick={handleRestoreVanilla}
                          disabled={importingExtra}
                          title="Restore vanilla"
                        >
                          ×
                        </button>
                      )}
                    </div>
                    <div className="costume-info">
                      <h4>{isVanilla ? 'Vanilla' : 'Custom'}</h4>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Available to Import section - shows ALL mods */}
            <div className="costumes-section">
              <div className="costumes-section-header">
                <h3>Available to Import</h3>
                <div className="batch-controls">
                  {selectedExtraMod && (
                    <button
                      className="btn-batch-import"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('start'); handleImportExtra(); }}
                      disabled={importingExtra}
                    >
                      {importingExtra ? 'Importing...' : 'Import Selected'}
                    </button>
                  )}
                </div>
              </div>
              <div className="costume-list">
                {availableMods.slice(modsPager.start, modsPager.end).map(mod => (
                  <div
                    key={mod.id}
                    className={`costume-card ${selectedExtraMod?.id === mod.id ? 'selected' : ''}`}
                    onClick={() => setSelectedExtraMod(mod)}
                  >
                    <div className="costume-preview" style={{ padding: '8px' }}>
                      <ExtraPreview extraType={selectedExtraType} modifications={mod.modifications} mod={mod} compact />
                      <input
                        type="checkbox"
                        className="costume-checkbox"
                        checked={selectedExtraMod?.id === mod.id}
                        readOnly
                      />
                    </div>
                    <div className="costume-info">
                      <h4>{mod.name}</h4>
                    </div>
                  </div>
                ))}
                {availableMods.length === 0 && (
                  <div className="no-costumes">
                    <p>No extras in vault. Create some in Storage → {selectedFighter.name} → Extras.</p>
                  </div>
                )}
              </div>
              <PaginationBar pager={modsPager} />
            </div>
          </>
        ) : (
          <div className="no-selection">
            <p>Select an extra type</p>
          </div>
        )}
      </div>

      {/* Import Loading Overlay */}
      {importingExtra && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader className="import-loader" size={104} label="Importing extra" />
            <h3>Importing...</h3>
            <p className="import-status">Please wait...</p>
          </div>
        </div>
      )}
    </div>
  )
}
