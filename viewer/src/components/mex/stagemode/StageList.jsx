/**
 * StageList - left panel of StageMode: mode toggle buttons,
 * DAS stage list with variant counts, and the Custom Stages slot.
 */
import { playSound, playHoverSound } from '../../../utils/sounds'
import { DAS_STAGES } from './useStageVariants'

export default function StageList({ mode, onModeChange, sm, cs }) {
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
        <span className="fighters-count">{DAS_STAGES.length}</span>
      </div>
      <div className="fighter-items">
        {DAS_STAGES.map(stage => {
          const availableVariants = sm.getVariantsForStage(stage.code)
          const mexCount = sm.mexVariantCounts[stage.code] || 0
          return (
            <div
              key={stage.code}
              className={`fighter-item ${sm.selectedStage?.code === stage.code ? 'selected' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); sm.setSelectedStage(stage); }}
            >
              <div className="fighter-name">{stage.name}</div>
              <div className="fighter-info">
                <span className="costume-count">{mexCount} in MEX</span>
                {availableVariants.length > 0 && (
                  <span className="available-count">{availableVariants.length} available</span>
                )}
              </div>
            </div>
          )
        })}
        <div
          className={`fighter-item ${sm.selectedStage?.isCustom ? 'selected' : ''}`}
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); sm.setSelectedStage({ code: 'custom', name: 'Custom Stages', isCustom: true }); }}
        >
          <div className="fighter-name">Custom Stages</div>
          <div className="fighter-info">
            <span className="costume-count">{cs.projectCustomStages.length} in ISO</span>
            {cs.vaultStages.length > 0 && (
              <span className="available-count">{cs.vaultStages.length} available</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
