/**
 * CostumesPanel - right panel of CharacterMode: "In ISO" costume list
 * (with drag-drop reordering and team color assignment) and the
 * "Available to Import" list with batch selection controls.
 *
 * Receives the useCostumes hook result as `cm` (costume manager).
 */
import { hasExtras } from '../../../config/extraTypes'
import { playSound, playHoverSound } from '../../../utils/sounds'
import HexagonLoader from '../../shared/HexagonLoader'

export default function CostumesPanel({ selectedFighter, refreshing, cm, API_URL, onEnterExtras }) {
  const {
    mexCostumes,
    loadingFighter,
    dataReady,
    removing,
    selectedCostumes,
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
    clearSelection
  } = cm

  return (
    <div className={`costumes-panel ${refreshing || loadingFighter ? 'refreshing' : ''}`}>
      {selectedFighter ? (
        <>
          <div className="costumes-section">
            <div className="costumes-section-header">
              <h3>In ISO ({dataReady ? mexCostumes.length : 'Loading...'})</h3>
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
              {mexCostumes.map((costume, idx) => {
                const isDragging = draggedIndex === idx
                const isDragOver = dragOverIndex === idx
                const costumeTeamColors = getCostumeTeamColor(idx)
                const isTeamAssignable = selectedTeamColor !== null
                return (
                  <div
                    key={idx}
                    className={`costume-card existing-costume ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''} ${dataReady ? 'card-visible' : 'card-hidden'} ${isTeamAssignable ? 'team-assignable' : ''}`}
                    style={{ animationDelay: dataReady ? `${idx * 30}ms` : '0ms' }}
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
                Available to Import ({dataReady ? getCostumesForFighter(selectedFighter.name).length : 'Loading...'})
                {selectedCostumes.size > 0 && ` - ${selectedCostumes.size} selected`}
              </h3>
              <div className="batch-controls">
                {getCostumesForFighter(selectedFighter.name).length > 0 && (
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
                {hasExtras(selectedFighter.name) && (
                  <button
                    className="btn-extras-mode"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); onEnterExtras(); }}
                  >
                    Extras
                  </button>
                )}
              </div>
            </div>
            <div className={`costume-list ${loadingFighter ? 'processing' : ''}`} ref={availableListRef}>
              {getCostumesForFighter(selectedFighter.name).map((costume, idx) => {
                const isSelected = selectedCostumes.has(costume.zipPath)
                const cascadeDelay = (mexCostumes.length + idx) * 30
                return (
                  <div
                    key={idx}
                    className={`costume-card ${isSelected ? 'selected' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                    style={{ animationDelay: dataReady ? `${cascadeDelay}ms` : '0ms' }}
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
              {dataReady && getCostumesForFighter(selectedFighter.name).length === 0 && (
                <div className="no-costumes">
                  <p>No costumes available in storage for {selectedFighter.name}</p>
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="no-selection">
          <p>Select a fighter to view costumes</p>
        </div>
      )}
    </div>
  )
}
