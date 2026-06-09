/**
 * FighterList - left panel of CharacterMode: mode toggle buttons,
 * playable fighter list, and the Add Character button.
 */
import { playSound, playHoverSound } from '../../../utils/sounds'
import { BACKEND_URL } from '../../../config'

export default function FighterList({
  mode,
  onModeChange,
  playableFighters,
  selectedFighter,
  onSelectFighter,
  getCostumesForFighter,
  onRemoveFighter,
  onAddCharacter
}) {
  return (
    <div className="fighters-list">
      <div className="fighters-header">
        <div className="mode-toggle">
          <button
            className={`mode-toggle-btn ${mode === 'characters' ? 'active' : ''}`}
            onMouseEnter={playHoverSound}
            onClick={() => { if (mode !== 'characters') { playSound('boop'); onModeChange('characters'); } }}
          >
            Fighters
          </button>
          <button
            className={`mode-toggle-btn ${mode === 'stages' ? 'active' : ''}`}
            onMouseEnter={playHoverSound}
            onClick={() => { if (mode !== 'stages') { playSound('boop'); onModeChange('stages'); } }}
          >
            Stages
          </button>
          <button
            className={`mode-toggle-btn ${mode === 'menus' ? 'active' : ''}`}
            onMouseEnter={playHoverSound}
            onClick={() => { if (mode !== 'menus') { playSound('boop'); onModeChange('menus'); } }}
          >
            Menus
          </button>
        </div>
        <span className="fighters-count">{playableFighters.length}</span>
      </div>
      <div className="fighter-items">
        {playableFighters.map(fighter => {
          const availableCostumes = getCostumesForFighter(fighter.name)
          return (
            <div
              key={fighter.internalId}
              className={`fighter-item ${selectedFighter?.internalId === fighter.internalId ? 'selected' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); onSelectFighter(fighter); }}
            >
              {fighter.defaultStockUrl && (
                <img
                  src={`${BACKEND_URL}${fighter.defaultStockUrl}`}
                  alt=""
                  className="fighter-stock-icon"
                  onError={(e) => e.target.style.display = 'none'}
                />
              )}
              <div className="fighter-content">
                <div className="fighter-name">{fighter.name}</div>
                <div className="fighter-info">
                  <span className="costume-count">{fighter.costumeCount} in MEX</span>
                  {availableCostumes.length > 0 && (
                    <span className="available-count">{availableCostumes.length} available</span>
                  )}
                </div>
              </div>
              {fighter.isMexFighter && (
                <button
                  className="fighter-remove-btn"
                  title={`Remove ${fighter.name}`}
                  onClick={(e) => { e.stopPropagation(); onRemoveFighter(fighter.name); }}
                >
                  ×
                </button>
              )}
            </div>
          )
        })}
        <button
          className="add-character-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onAddCharacter(); }}
        >
          + Add Character
        </button>
      </div>
    </div>
  )
}
