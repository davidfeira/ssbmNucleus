/**
 * StageMode - MEX stage variant management with Dynamic Alternate Stages (DAS)
 *
 * Features:
 * - DAS framework installation
 * - Stage list with variant counts
 * - MEX variants panel with button token assignment
 * - Available variants panel with batch selection/import
 * - Button token UI for variant assignment
 *
 * Orchestrator component - state and UI live in ./stagemode/:
 * - useStageVariants: DAS install/fetch/import/remove/button-token logic
 * - useCustomStages: custom stage vault/project fetch/install/remove logic
 * - StageList, VariantsPanel, CustomStagesPanel: UI
 */
import ConfirmDialog from '../shared/ConfirmDialog'
import HexagonLoader from '../shared/HexagonLoader'
import useStageVariants from './stagemode/useStageVariants'
import useCustomStages from './stagemode/useCustomStages'
import StageList from './stagemode/StageList'
import VariantsPanel from './stagemode/VariantsPanel'
import CustomStagesPanel from './stagemode/CustomStagesPanel'

export default function StageMode({
  mode,
  onModeChange,
  onRefresh,
  refreshing,
  API_URL
}) {
  const sm = useStageVariants({ API_URL, onRefresh })
  const cs = useCustomStages({ API_URL, onRefresh })

  const batchImportProgress = sm.batchImporting && sm.batchProgress.total > 0
    ? (sm.batchProgress.current / sm.batchProgress.total) * 100
    : null

  return (
    <div className="mex-content">
      {!sm.dasInstalled ? (
        <div className="das-install-prompt">
          <h3>Dynamic Alternate Stages Not Installed</h3>
          <p>Install the DAS framework to manage alternate stage variants for your 6 competitive stages.</p>
          <button
            className="btn-primary"
            onClick={sm.installDAS}
            disabled={sm.dasChecking}
          >
            {sm.dasChecking ? 'Installing...' : 'Install DAS Framework'}
          </button>
        </div>
      ) : (
        <>
          <StageList mode={mode} onModeChange={onModeChange} sm={sm} cs={cs} />

          <div className={`costumes-panel ${refreshing ? 'refreshing' : ''}`}>
            {sm.selectedStage?.isCustom ? (
              <CustomStagesPanel cs={cs} />
            ) : sm.selectedStage ? (
              <VariantsPanel sm={sm} />
            ) : (
              <div className="no-selection">
                <p>Select a stage to view variants</p>
              </div>
            )}
          </div>

          {/* Import Loading Overlay */}
          {(sm.importing || sm.batchImporting) && (
            <div className="import-overlay">
              <div className="import-modal import-modal--hexagon">
                <HexagonLoader
                  className="import-loader"
                  size={112}
                  label="Importing stage variants"
                  progress={batchImportProgress}
                  minimumVisibleProgress={6}
                />
                <h3>Importing...</h3>
                <p className="import-status">Installing selected variants...</p>
              </div>
            </div>
          )}
        </>
      )}

      {cs.batchInstallingStages && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader
              className="import-loader"
              size={112}
              label="Adding stages"
              progress={cs.batchStageProgress.total > 0 ? (cs.batchStageProgress.current / cs.batchStageProgress.total) * 100 : null}
              minimumVisibleProgress={6}
            />
            <h3>Adding Stages...</h3>
            <p className="import-status">{cs.batchStageProgress.current} / {cs.batchStageProgress.total}</p>
          </div>
        </div>
      )}

      <ConfirmDialog
        show={sm.showConfirmDialog}
        title={sm.pendingRemoval?.bulk ? 'Remove Selected Variants' : 'Remove Variant'}
        message={sm.pendingRemoval
          ? (sm.pendingRemoval.bulk
              ? `Remove ${sm.pendingRemoval.items.length} selected stage variant(s) from the project?`
              : `Are you sure you want to remove "${sm.pendingRemoval.variantName}"?`)
          : ''}
        confirmText="Remove"
        onConfirm={sm.confirmRemoveVariant}
        onCancel={() => { sm.setShowConfirmDialog(false); sm.setPendingRemoval(null); }}
      />
    </div>
  )
}
