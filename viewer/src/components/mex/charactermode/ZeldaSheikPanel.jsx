/**
 * ZeldaSheikPanel - the combined Zelda/Sheik costumes panel.
 *
 * Zelda and Sheik are one in-game pairing: costume slot N of one loads slot N
 * of the other on transform. So when either fighter is selected, this panel
 * replaces the normal CostumesPanel with:
 *   - "In ISO": a slot-paired ladder -- each column is one in-game slot with
 *     the Zelda costume on top, the Sheik costume below, and a connector line
 *     between them (dashed red when one half is missing).
 *   - "Available to Import": split vertically, Zelda's storage skins on top,
 *     Sheik's below, sharing one batch-selection toolbar.
 *
 * Receives the useCostumes hook result as `cm` (same contract as CostumesPanel).
 */
import { useState } from 'react'
import { playSound, playHoverSound } from '../../../utils/sounds'
import HexagonLoader from '../../shared/HexagonLoader'
import PaginationBar from '../../shared/PaginationBar'
import usePagination from '../../shared/usePagination'
import SoundPacksModal from '../../storage/SoundPacksModal'
import { ZS_PAIR } from './useCostumes'

const SoundIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
  </svg>
)

export default function ZeldaSheikPanel({ refreshing, cm, API_URL }) {
  const {
    pairCostumes,
    loadingFighter,
    dataReady,
    removing,
    selectedCostumes,
    batchImporting,
    batchProgress,
    draggedIndex,
    dragOverIndex,
    draggedRow,
    reordering,
    selectedTeamColor,
    availableListRef,
    handleTeamColorClick,
    handlePairCostumeTeamAssign,
    getPairCostumeTeamColor,
    handleRemoveCostume,
    handleBatchImport,
    handlePairDragStart,
    handleDragOver,
    handlePairDragEnter,
    handleDragLeave,
    handlePairDrop,
    handleDragEnd,
    getCostumesForFighter,
    toggleCostumeSelection,
    selectAllCostumes,
    clearSelection
  } = cm

  const BASE_URL = API_URL.replace('/api/mex', '')
  // Zelda and Sheik share one sound bank (zs.ssm) — one pack covers both
  const [showSoundBank, setShowSoundBank] = useState(false)
  const zelda = pairCostumes.Zelda || []
  const sheik = pairCostumes.Sheik || []
  const slotCount = Math.max(zelda.length, sheik.length)
  const mismatch = dataReady && zelda.length !== sheik.length
  const isTeamAssignable = selectedTeamColor !== null
  const availableTotal = ZS_PAIR.reduce((n, name) => n + getCostumesForFighter(name).length, 0)

  // Pagination: the ladder pages by SLOT (each slot column = a Zelda/Sheik
  // pair), the two available sub-lists page independently. Hooks are called
  // unconditionally in a fixed order (never inside the ZS_PAIR.map loop).
  const ladderPager = usePagination(slotCount, 'zs-ladder')
  const availPagers = {
    Zelda: usePagination(getCostumesForFighter('Zelda').length, 'zs-avail-zelda'),
    Sheik: usePagination(getCostumesForFighter('Sheik').length, 'zs-avail-sheik')
  }

  // An unpaired slot doesn't crash in game (verified live): transforming there
  // just loads the fighter's FIRST costume instead. So instead of a bare "no
  // half" placeholder, show a ghosted preview of that actual fallback.
  const renderFallbackSlot = (fighterName, slotNum) => {
    const fallback = (pairCostumes[fighterName] || [])[0]
    const fbName = fallback?.name || 'Default'
    return (
      <div
        className="zs-empty-slot"
        title={`No ${fighterName} costume in slot ${slotNum} — transforming here loads ${fighterName}'s first costume (${fbName}) instead. Safe, no crash.`}
      >
        {fallback?.cspUrl ? (
          <>
            <img
              className="zs-fallback-csp"
              src={`${BASE_URL}${fallback.cspUrl}`}
              alt=""
              onError={(e) => e.target.style.display = 'none'}
            />
            <span className="zs-fallback-tag">transforms to</span>
            <span className="zs-fallback-name">{fbName}</span>
          </>
        ) : (
          <span>no {fighterName} half</span>
        )}
      </div>
    )
  }

  const renderInIsoTile = (fighterName, costume, idx, animDelay) => {
    const isDragging = draggedRow === fighterName && draggedIndex === idx
    const isDragOver = draggedRow === fighterName && dragOverIndex === idx
    const teamColorsOn = getPairCostumeTeamColor(fighterName, idx)
    return (
      <div
        className={`costume-card existing-costume ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''} ${dataReady ? 'card-visible' : 'card-hidden'} ${isTeamAssignable ? 'team-assignable' : ''}`}
        style={{ animationDelay: dataReady ? `${animDelay}ms` : '0ms' }}
        draggable={!removing && !reordering && !isTeamAssignable}
        onMouseEnter={playHoverSound}
        onClick={isTeamAssignable ? () => handlePairCostumeTeamAssign(fighterName, idx) : undefined}
        onDragStart={(e) => !isTeamAssignable && handlePairDragStart(e, fighterName, idx)}
        onDragOver={handleDragOver}
        onDragEnter={(e) => handlePairDragEnter(e, fighterName, idx)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handlePairDrop(e, fighterName, idx)}
        onDragEnd={handleDragEnd}
      >
        <div className="costume-preview">
          <span className={`zs-fighter-tag zs-${fighterName.toLowerCase()}`}>{fighterName}</span>
          {costume.cspUrl && (
            <img
              src={`${BASE_URL}${costume.cspUrl}`}
              alt={costume.name}
              onError={(e) => e.target.style.display = 'none'}
            />
          )}
          <button
            className="btn-remove"
            onClick={(e) => {
              e.stopPropagation()
              handleRemoveCostume(fighterName, idx, costume.name)
            }}
            disabled={removing}
            title="Remove costume"
          >
            ×
          </button>
          {costume.iconUrl && (
            <div className="stock-icon-overlay">
              <img
                src={`${BASE_URL}${costume.iconUrl}`}
                alt="Stock"
                onError={(e) => e.target.style.display = 'none'}
              />
            </div>
          )}
          {teamColorsOn.length > 0 && (
            <div className="team-color-badges">
              {teamColorsOn.map(color => (
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
  }

  return (
    <div className={`costumes-panel ${refreshing || loadingFighter ? 'refreshing' : ''}`}>
      <div className="costumes-section">
        <div className="costumes-section-header">
          <h3>
            In ISO — Zelda ({dataReady ? zelda.length : '…'}) / Sheik ({dataReady ? sheik.length : '…'})
          </h3>
          {mismatch && (
            <span
              className="zs-mismatch"
              title="Zelda and Sheik have different costume counts. Slot N of one transforms into slot N of the other; an unpaired slot still works (verified in-game, no crash) — the transform just appears as the default first costume, and transforming back returns to the correct skin."
            >
              ⚠ unpaired slots
            </span>
          )}
          <div className="iso-mod-actions">
            <button
              className="btn-pose-all btn-sound-pack"
              onClick={() => { playSound('boop'); setShowSoundBank(true); }}
              onMouseEnter={playHoverSound}
              title="Sound packs — Zelda and Sheik share one sound bank; choose which pack this project uses"
            >
              <SoundIcon />
            </button>
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
                title={`${c.id.charAt(0).toUpperCase() + c.id.slice(1)} Team - click a Zelda or Sheik costume to assign`}
              >
                {c.label}
              </div>
            ))}
          </div>
        </div>
        <div className={`costume-list existing zs-ladder ${reordering ? 'processing' : ''} ${loadingFighter ? 'processing' : ''}`}>
          {Array.from({ length: ladderPager.end - ladderPager.start }, (_, col) => {
            const i = ladderPager.start + col
            const zc = zelda[i]
            const sc = sheik[i]
            const paired = !!(zc && sc)
            return (
              <div className="zs-pair-column" key={i}>
                {zc
                  ? renderInIsoTile('Zelda', zc, i, Math.min(col * 30, 990))
                  : renderFallbackSlot('Zelda', i + 1)}
                <div
                  className={`zs-pair-link ${paired ? '' : 'broken'}`}
                  title={paired
                    ? `Slot ${i + 1}: this Zelda and Sheik transform into each other`
                    : `Slot ${i + 1}: missing the ${zc ? 'Sheik' : 'Zelda'} half — the transform shows the default costume instead (safe, no crash)`}
                >
                  <span className="zs-slot-num">{i + 1}</span>
                </div>
                {sc
                  ? renderInIsoTile('Sheik', sc, i, Math.min(col * 30 + 15, 990))
                  : renderFallbackSlot('Sheik', i + 1)}
              </div>
            )
          })}
          {dataReady && slotCount === 0 && (
            <div className="no-costumes">
              <p>No costumes in MEX yet</p>
            </div>
          )}
        </div>
        <PaginationBar pager={ladderPager} />
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
            Available to Import ({dataReady ? availableTotal : 'Loading...'})
            {selectedCostumes.size > 0 && ` - ${selectedCostumes.size} selected`}
          </h3>
          <div className="batch-controls">
            {availableTotal > 0 && (
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
        <div className="zs-available-body" ref={availableListRef}>
          {ZS_PAIR.map((fighterName) => {
            const available = getCostumesForFighter(fighterName)
            const pager = availPagers[fighterName]
            return (
              <div className="zs-available-sub" key={fighterName}>
                <div className={`zs-sub-label zs-${fighterName.toLowerCase()}`}>
                  {fighterName} ({dataReady ? available.length : '…'})
                </div>
                <div className={`costume-list ${loadingFighter ? 'processing' : ''}`}>
                  {available.slice(pager.start, pager.end).map((costume, i) => {
                    const idx = pager.start + i
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
                              src={`${BASE_URL}${costume.cspUrl}`}
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
                                src={`${BASE_URL}${costume.stockUrl}`}
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
                  {dataReady && available.length === 0 && (
                    <div className="no-costumes">
                      <p>No costumes available in storage for {fighterName}</p>
                    </div>
                  )}
                </div>
                <PaginationBar pager={pager} />
              </div>
            )
          })}
        </div>
      </div>

      <SoundPacksModal
        show={showSoundBank}
        character="Zelda"
        displayName="Zelda / Sheik"
        installMode
        API_URL={API_URL}
        onClose={() => setShowSoundBank(false)}
      />
    </div>
  )
}
