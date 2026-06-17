/**
 * CostumesPanel - right panel of CharacterMode: "In ISO" costume list
 * (with drag-drop reordering and team color assignment) and the
 * "Available to Import" list with batch selection controls.
 *
 * Receives the useCostumes hook result as `cm` (costume manager).
 */
import { useState } from 'react'
import { hasExtras } from '../../../config/extraTypes'
import { playSound, playHoverSound } from '../../../utils/sounds'
import HexagonLoader from '../../shared/HexagonLoader'
import PaginationBar from '../../shared/PaginationBar'
import usePagination from '../../shared/usePagination'
import SoundPacksModal from '../../storage/SoundPacksModal'
import ZeldaSheikPanel from './ZeldaSheikPanel'
import { isZeldaSheikName } from './useCostumes'

const PoseIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
    <circle cx="12" cy="13" r="4"/>
  </svg>
)

const SoundIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
  </svg>
)

// vanilla characters with a vault sound pack (fighter SSM bank); custom
// fighters edit their bank from the custom character detail page instead
const SOUND_PACK_CHARS = new Set([
  'bowser', 'c. falcon', 'captain falcon', 'dk', 'donkey kong', 'dr. mario',
  'falco', 'fox', 'ganondorf', 'ice climbers', 'jigglypuff', 'kirby', 'link',
  'luigi', 'mario', 'marth', 'mewtwo', 'mr. game & watch', 'game & watch',
  'ness', 'peach', 'pichu', 'pikachu', 'roy', 'samus', 'sheik', 'yoshi',
  'young link', 'zelda',
])

export const hasSoundPack = (name) => SOUND_PACK_CHARS.has((name || '').toLowerCase())

const PER_FIGHTER_COSTUME_CAP = 255

export default function CostumesPanel({ selectedFighter, refreshing, cm, API_URL, onEnterExtras, onApplyPose }) {
  const {
    mexCostumes,
    loadingFighter,
    dataReady,
    removing,
    selectedCostumes,
    selectedInstalledCostumes,
    batchImporting,
    batchProgress,
    draggedIndex,
    dragOverIndex,
    reordering,
    selectedTeamColor,
    availableListRef,
    handleTeamColorClick,
    handleCostumeTeamAssign,
    getCostumeTeamColor,
    handleRemoveCostume,
    handleBatchRemoveCostumes,
    handleBatchImport,
    handleDragStart,
    handleDragOver,
    handleDragEnter,
    handleDragLeave,
    handleDrop,
    handleDragEnd,
    getCostumesForFighter,
    toggleCostumeSelection,
    selectAllCostumes,
    clearSelection,
    installedCostumeKey,
    toggleInstalledCostumeSelection,
    clearInstalledCostumeSelection
  } = cm

  // Sound pack browser (vanilla character SSM bank, stored in the vault and
  // installed into the ISO at export)
  const [showSoundBank, setShowSoundBank] = useState(false)

  // Zelda and Sheik share their in-game costume slots (transform pairing), so
  // selecting EITHER shows the combined slot-paired panel instead. The check
  // lives BELOW the pagination hooks so the hook order is stable across renders.
  const isZS = selectedFighter && isZeldaSheikName(selectedFighter.name)
  const availableCostumes = selectedFighter && !isZS
    ? getCostumesForFighter(selectedFighter.name)
    : []
  const inIsoPager = usePagination(mexCostumes.length, `${selectedFighter?.name}-iso`)
  const availPager = usePagination(availableCostumes.length, `${selectedFighter?.name}-avail`)

  if (isZS) {
    return (
      <ZeldaSheikPanel
        refreshing={refreshing}
        cm={cm}
        API_URL={API_URL}
        selectedFighter={selectedFighter}
        onEnterExtras={onEnterExtras}
        onApplyPose={onApplyPose}
      />
    )
  }

  return (
    <div className={`costumes-panel ${refreshing || loadingFighter ? 'refreshing' : ''}`}>
      {selectedFighter ? (
        <>
          <div className="costumes-section">
            <div className="costumes-section-header">
              <h3>
                In ISO ({dataReady ? `${mexCostumes.length}/${PER_FIGHTER_COSTUME_CAP}` : 'Loading...'})
                {selectedInstalledCostumes.size > 0 && ` - ${selectedInstalledCostumes.size} selected`}
              </h3>
              <div className="iso-mod-actions">
                {selectedInstalledCostumes.size > 0 && (
                  <>
                    <button
                      className="btn-batch-import btn-batch-delete"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('start'); handleBatchRemoveCostumes(); }}
                      disabled={removing || reordering || selectedTeamColor !== null}
                    >
                      Delete Selected ({selectedInstalledCostumes.size})
                    </button>
                    <button
                      className="btn-clear-selection"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); clearInstalledCostumeSelection(); }}
                      disabled={removing || reordering}
                    >
                      Clear
                    </button>
                  </>
                )}
                {hasExtras(selectedFighter.name) && (
                  <button
                    className="btn-extras-mode"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); onEnterExtras(); }}
                  >
                    Extras
                  </button>
                )}
                {onApplyPose && (
                  <button
                    className="btn-pose-all"
                    onClick={() => { playSound('boop'); onApplyPose(); }}
                    onMouseEnter={playHoverSound}
                    disabled={!dataReady || mexCostumes.length === 0}
                    title="Apply a pose to all portraits"
                  >
                    <PoseIcon />
                  </button>
                )}
                {hasSoundPack(selectedFighter.name) && (
                  <button
                    className="btn-pose-all btn-sound-pack"
                    onClick={() => { playSound('boop'); setShowSoundBank(true); }}
                    onMouseEnter={playHoverSound}
                    title="Sound packs — choose which voice/SFX pack this project uses"
                  >
                    <SoundIcon />
                  </button>
                )}
              </div>
              <div className="team-color-tokens">
                {[
                  { id: 'red', label: 'R', color: '#ff4757' },
                  { id: 'blue', label: 'B', color: '#3742fa' },
                  { id: 'green', label: 'G', color: '#2ed573' }
                ].map(c => (
                  <div
                    key={c.id}
                    className={`team-color-token ${selectedTeamColor === c.id ? 'selected' : ''}`}
                    style={{ '--token-color': c.color }}
                    onClick={() => handleTeamColorClick(c.id)}
                    onMouseEnter={playHoverSound}
                    title={`${c.id.charAt(0).toUpperCase() + c.id.slice(1)} Team - click to assign`}
                  >
                    {c.label}
                  </div>
                ))}
              </div>
            </div>
            <div className={`costume-list existing ${reordering ? 'processing' : ''} ${loadingFighter ? 'processing' : ''}`}>
              {mexCostumes.slice(inIsoPager.start, inIsoPager.end).map((costume, i) => {
                const idx = inIsoPager.start + i
                const isDragging = draggedIndex === idx
                const isDragOver = dragOverIndex === idx
                const costumeTeamColors = getCostumeTeamColor(idx)
                const isTeamAssignable = selectedTeamColor !== null
                const isDeleteSelected = selectedInstalledCostumes.has(installedCostumeKey(selectedFighter.name, idx))
                return (
                  <div
                    key={idx}
                    className={`costume-card existing-costume ${isDeleteSelected ? 'selected' : ''} ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''} ${dataReady ? 'card-visible' : 'card-hidden'} ${isTeamAssignable ? 'team-assignable' : ''}`}
                    style={{ animationDelay: dataReady ? `${Math.min(i * 30, 990)}ms` : '0ms' }}
                    draggable={!removing && !reordering && !isTeamAssignable}
                    onMouseEnter={playHoverSound}
                    onClick={isTeamAssignable ? () => handleCostumeTeamAssign(idx) : undefined}
                    onDragStart={(e) => !isTeamAssignable && handleDragStart(e, idx)}
                    onDragOver={handleDragOver}
                    onDragEnter={(e) => handleDragEnter(e, idx)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, idx)}
                    onDragEnd={handleDragEnd}
                  >
                    <div className="costume-preview">
                      <input
                        type="checkbox"
                        className="costume-checkbox"
                        checked={isDeleteSelected}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => { playSound('boop'); toggleInstalledCostumeSelection(selectedFighter.name, idx); }}
                        disabled={removing || reordering || isTeamAssignable}
                        title="Select for delete"
                      />
                      {costume.cspUrl && (
                        <img
                          src={`${API_URL.replace('/api/mex', '')}${costume.cspUrl}`}
                          alt={costume.name}
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      )}
                      <button
                        className="btn-remove"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRemoveCostume(selectedFighter.name, idx, costume.name)
                        }}
                        disabled={removing}
                        title="Remove costume"
                      >
                        ×
                      </button>
                      {costume.iconUrl && (
                        <div className="stock-icon-overlay">
                          <img
                            src={`${API_URL.replace('/api/mex', '')}${costume.iconUrl}`}
                            alt="Stock"
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        </div>
                      )}
                      {/* Team color badges */}
                      {costumeTeamColors.length > 0 && (
                        <div className="team-color-badges">
                          {costumeTeamColors.map(color => (
                            <div
                              key={color}
                              className={`team-color-badge team-${color}`}
                              title={`${color.charAt(0).toUpperCase() + color.slice(1)} Team`}
                            >
                              {color[0].toUpperCase()}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="costume-info">
                      <h4>{costume.name}</h4>
                    </div>
                  </div>
                )
              })}
              {dataReady && mexCostumes.length === 0 && (
                <div className="no-costumes">
                  <p>No costumes in MEX yet</p>
                </div>
              )}
            </div>
            <PaginationBar pager={inIsoPager} />
            {reordering && (
              <div className="reorder-overlay">
                <HexagonLoader className="reorder-loader" size={46} decorative />
                <span>Reordering...</span>
              </div>
            )}
          </div>

          <div className="costumes-section">
            <div className="costumes-section-header">
              <h3>
                Available to Import ({dataReady ? availableCostumes.length : 'Loading...'})
                {selectedCostumes.size > 0 && ` - ${selectedCostumes.size} selected`}
              </h3>
              <div className="batch-controls">
                {availableCostumes.length > 0 && (
                  <button
                    className="btn-select-all"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); selectAllCostumes(); }}
                    disabled={loadingFighter || batchImporting}
                  >
                    Select All
                  </button>
                )}
                {selectedCostumes.size > 0 && (
                  <>
                    <button
                      className="btn-batch-import"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('start'); handleBatchImport(); }}
                      disabled={batchImporting || loadingFighter}
                    >
                      {batchImporting
                        ? `Importing ${batchProgress.current}/${batchProgress.total}...`
                        : `Import All Selected (${selectedCostumes.size})`}
                    </button>
                    <button
                      className="btn-clear-selection"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); clearSelection(); }}
                      disabled={batchImporting || loadingFighter}
                    >
                      Clear
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className={`costume-list ${loadingFighter ? 'processing' : ''}`} ref={availableListRef}>
              {availableCostumes.slice(availPager.start, availPager.end).map((costume, i) => {
                const idx = availPager.start + i
                const isSelected = selectedCostumes.has(costume.zipPath)
                return (
                  <div
                    key={idx}
                    className={`costume-card ${isSelected ? 'selected' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                    style={{ animationDelay: dataReady ? `${Math.min(i * 30, 990)}ms` : '0ms' }}
                    onMouseEnter={playHoverSound}
                    onClick={() => { if (!batchImporting && !loadingFighter) { playSound('boop'); toggleCostumeSelection(costume.zipPath); } }}
                  >
                    <div className="costume-preview">
                      {costume.cspUrl && (
                        <img
                          src={`${API_URL.replace('/api/mex', '')}${costume.cspUrl}`}
                          alt={costume.name}
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      )}
                      <input
                        type="checkbox"
                        className="costume-checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        disabled={batchImporting || loadingFighter}
                      />
                      {costume.stockUrl && (
                        <div className="stock-icon-overlay">
                          <img
                            src={`${API_URL.replace('/api/mex', '')}${costume.stockUrl}`}
                            alt="Stock"
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        </div>
                      )}
                      {costume.slippiSafe && (
                        <div className="slippi-badge slippi-badge-overlay" title="Slippi Safe">
                          ✓
                        </div>
                      )}
                    </div>
                    <div className="costume-info">
                      <h4>{costume.name?.includes(' - ') ? costume.name.split(' - ').slice(1).join(' - ') : costume.name}</h4>
                    </div>
                  </div>
                )
              })}
              {dataReady && availableCostumes.length === 0 && (
                <div className="no-costumes">
                  <p>No costumes available in storage for {selectedFighter.name}</p>
                </div>
              )}
            </div>
            <PaginationBar pager={availPager} />
          </div>

          <SoundPacksModal
            show={showSoundBank}
            character={selectedFighter.name}
            displayName={selectedFighter.name}
            installMode
            API_URL={API_URL}
            onClose={() => setShowSoundBank(false)}
          />
        </>
      ) : (
        <div className="no-selection">
          <p>Select a fighter to view costumes</p>
        </div>
      )}
    </div>
  )
}
