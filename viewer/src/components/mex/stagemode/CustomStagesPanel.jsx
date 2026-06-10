/**
 * CustomStagesPanel - custom stages view of StageMode: stages installed
 * in the ISO and vault stages available to import (with batch controls).
 */
import { playSound, playHoverSound } from '../../../utils/sounds'
import { BACKEND_URL } from '../../../config'
import PaginationBar from '../../shared/PaginationBar'
import usePagination from '../../shared/usePagination'

export default function CustomStagesPanel({ cs }) {
  const inIsoPager = usePagination(cs.projectCustomStages.length, 'custom-iso')
  const vaultPager = usePagination(cs.vaultStages.length, 'custom-vault')
  return (
    <>
      <div className="costumes-section">
        <div className="costumes-section-header">
          <h3>In ISO ({cs.projectCustomStages.length})</h3>
        </div>
        <div className="costume-list existing">
          {cs.projectCustomStages.slice(inIsoPager.start, inIsoPager.end).map((stage, i) => (
            <div key={stage.index} className="costume-card existing-costume card-visible" style={{ animationDelay: `${Math.min(i * 30, 990)}ms` }}>
              <div className="costume-preview">
                {stage.icon_url && (
                  <img src={`${BACKEND_URL}${stage.icon_url}`} alt={stage.name} style={{ imageRendering: 'pixelated' }} onError={e => e.target.style.display = 'none'} />
                )}
                <button className="btn-remove" onClick={() => cs.handleRemoveCustomStage(stage.name)} title="Remove stage">×</button>
              </div>
              <div className="costume-info"><h4>{stage.name}</h4></div>
            </div>
          ))}
          {cs.projectCustomStages.length === 0 && (
            <div className="no-costumes"><p>No custom stages installed</p></div>
          )}
        </div>
        <PaginationBar pager={inIsoPager} />
      </div>
      <div className="costumes-section">
        <div className="costumes-section-header">
          <h3>
            Available to Import ({cs.vaultStages.length})
            {cs.selectedCustomStages.size > 0 && ` - ${cs.selectedCustomStages.size} selected`}
          </h3>
          {cs.vaultStages.length > 0 && (
            <div className="batch-controls">
              {cs.selectedCustomStages.size > 0 ? (
                <>
                  <button
                    className="btn-batch-import"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); cs.handleBatchInstallStages(); }}
                    disabled={cs.batchInstallingStages}
                  >
                    {cs.batchInstallingStages
                      ? `Installing ${cs.batchStageProgress.current}/${cs.batchStageProgress.total}...`
                      : `Install Selected (${cs.selectedCustomStages.size})`}
                  </button>
                  <button
                    className="btn-clear-selection"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); cs.clearCustomStageSelection(); }}
                    disabled={cs.batchInstallingStages}
                  >
                    Clear
                  </button>
                </>
              ) : (
                <button
                  className="btn-select-all"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); cs.selectAllCustomStages(); }}
                >
                  Select All
                </button>
              )}
            </div>
          )}
        </div>
        <div className="costume-list">
          {cs.vaultStages.slice(vaultPager.start, vaultPager.end).map((stage, i) => {
            const isSelected = cs.selectedCustomStages.has(stage.slug)
            return (
              <div
                key={stage.slug}
                className={`costume-card card-visible ${isSelected ? 'selected' : ''}`}
                style={{ animationDelay: `${Math.min(i * 30, 990)}ms` }}
                onMouseEnter={playHoverSound}
                onClick={() => { if (!cs.batchInstallingStages) { playSound('boop'); cs.toggleCustomStageSelection(stage.slug); } }}
              >
                <div className="costume-preview">
                  {stage.has_icon && (
                    <img src={`${BACKEND_URL}${stage.icon_url}`} alt={stage.name} style={{ imageRendering: 'pixelated' }} onError={e => e.target.style.display = 'none'} />
                  )}
                  <input
                    type="checkbox"
                    className="costume-checkbox"
                    checked={isSelected}
                    onChange={() => {}}
                    disabled={cs.batchInstallingStages}
                  />
                </div>
                <div className="costume-info">
                  <h4>{stage.name}</h4>
                </div>
              </div>
            )
          })}
          {cs.vaultStages.length === 0 && (
            <div className="no-costumes"><p>No custom stages in vault</p></div>
          )}
        </div>
        <PaginationBar pager={vaultPager} />
      </div>
    </>
  )
}
