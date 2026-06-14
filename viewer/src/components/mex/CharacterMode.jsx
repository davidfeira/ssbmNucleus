/**
 * CharacterMode - MEX character costume management
 *
 * Features:
 * - Fighter list with costume counts
 * - MEX costumes panel with drag-drop reordering
 * - Available costumes panel with batch selection/import
 * - Ice Climbers special handling (auto-pair Popo/Nana)
 * - Single and batch costume import/removal
 * - Extras mode for managing character extras (laser colors, etc.)
 *
 * Orchestrator component - state and UI live in ./charactermode/:
 * - useCostumes: costume fetch/import/remove/reorder/team-color logic
 * - useExtras: extras mode state and API logic
 * - useCustomCharacters: add/remove custom character logic
 * - FighterList, CostumesPanel, AddCharacterModal, ExtrasView: UI
 */
import ConfirmDialog from '../shared/ConfirmDialog'
import HexagonLoader from '../shared/HexagonLoader'
import PoseManagerModal from '../storage/PoseManagerModal'
import useCostumes from './charactermode/useCostumes'
import useExtras from './charactermode/useExtras'
import useCustomCharacters from './charactermode/useCustomCharacters'
import useApplyPose from './charactermode/useApplyPose'
import FighterList from './charactermode/FighterList'
import CostumesPanel from './charactermode/CostumesPanel'
import AddCharacterModal from './charactermode/AddCharacterModal'
import ExtrasView from './charactermode/ExtrasView'

export default function CharacterMode({
  mode,
  onModeChange,
  fighters,
  selectedFighter,
  onSelectFighter,
  storageCostumes,
  onRefresh,
  refreshing,
  API_URL
}) {
  const cm = useCostumes({ API_URL, fighters, storageCostumes, selectedFighter, onRefresh })
  const extras = useExtras({ API_URL, selectedFighter })
  const cc = useCustomCharacters({ API_URL, onRefresh })
  const ap = useApplyPose({
    API_URL,
    selectedFighter,
    // Pose can target a fighter other than the selected one (Zelda/Sheik split),
    // so refresh whichever fighter was actually posed.
    refreshCostumes: (name) => {
      const fighterName = name || selectedFighter?.name
      return fighterName ? cm.refreshMexCostumes(fighterName) : Promise.resolve()
    }
  })

  // The fighter a pose targets, and its in-ISO costume count, for the modal/
  // confirm text. For Zelda/Sheik the count comes from that half's pair list.
  const poseFighterName = ap.poseFighter?.name || selectedFighter?.name || ''
  const poseCostumeCount = ap.poseFighter && cm.isZeldaSheik
    ? (cm.pairCostumes[ap.poseFighter.name]?.length ?? 0)
    : cm.mexCostumes.length

  // Extras mode UI
  if (extras.extrasMode && selectedFighter) {
    return <ExtrasView selectedFighter={selectedFighter} extras={extras} />
  }

  // Character mode UI (default)
  // Hide non-playable characters
  const hiddenCharacters = ['Nana', 'Master Hand', 'Crazy Hand', 'Wireframe Male', 'Wireframe Female', 'Giga Bowser', 'Sandbag', 'NONE']
  const playableFighters = fighters.filter(f => !hiddenCharacters.includes(f.name))
  const batchImportProgress = cm.batchImporting && cm.batchProgress.total > 0
    ? (cm.batchProgress.current / cm.batchProgress.total) * 100
    : null

  return (
    <div className="mex-content">
      <FighterList
        mode={mode}
        onModeChange={onModeChange}
        playableFighters={playableFighters}
        selectedFighter={selectedFighter}
        onSelectFighter={onSelectFighter}
        getCostumesForFighter={cm.getCostumesForFighter}
        onRemoveFighter={cc.handleRemoveFighter}
        onAddCharacter={cc.openAddCharacterModal}
      />

      <AddCharacterModal cc={cc} />

      <CostumesPanel
        selectedFighter={selectedFighter}
        refreshing={refreshing}
        cm={cm}
        API_URL={API_URL}
        onEnterExtras={() => extras.setExtrasMode(true)}
        onApplyPose={ap.openPoseModal}
      />

      {/* Pose picker for "apply pose to all installed costumes" */}
      <PoseManagerModal
        show={ap.showPoseModal}
        character={ap.poseCharacter || poseFighterName}
        displayName={poseFighterName}
        baseSkinId={ap.poseBaseSkinId || undefined}
        onSelectPose={ap.handlePoseSelected}
        onClose={() => ap.setShowPoseModal(false)}
        API_URL={API_URL}
      />

      {/* Import Loading Overlay */}
      {(cm.importing || cm.batchImporting) && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader
              className="import-loader"
              size={112}
              label="Importing costumes"
              progress={batchImportProgress}
              minimumVisibleProgress={6}
            />
            <h3>Importing...</h3>
            <p className="import-status">Please wait...</p>
          </div>
        </div>
      )}

      {/* Apply-pose progress overlay */}
      {ap.applying && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader
              className="import-loader"
              size={112}
              label={ap.applyingPose?.isOriginal ? 'Restoring portraits' : 'Applying pose'}
              progress={ap.applyProgress.total > 0
                ? ((ap.applyProgress.current - 1) / ap.applyProgress.total) * 100
                : null}
              minimumVisibleProgress={6}
            />
            <h3>{ap.applyingPose?.isOriginal ? 'Restoring Portraits...' : 'Applying Pose...'}</h3>
            <p className="import-status">
              {ap.applyProgress.total > 0
                ? (ap.applyingPose?.isOriginal
                    ? `${ap.applyProgress.current} / ${ap.applyProgress.total}`
                    : `${ap.applyProgress.current} / ${ap.applyProgress.total} — missing portraits are rendered and saved to the vault`)
                : 'Matching costumes to vault skins...'}
            </p>
          </div>
        </div>
      )}

      <ConfirmDialog
        show={!!ap.pendingPose}
        title={ap.pendingPose?.isOriginal ? 'Restore Original Portraits' : 'Apply Pose'}
        message={ap.pendingPose
          ? (ap.pendingPose.isOriginal
              ? `Restore the original portraits for all ${poseCostumeCount} ${poseFighterName} costumes? Each one goes back to its vault skin's main CSP (or the vanilla portrait).`
              : `Apply pose "${ap.pendingPose.name}" to all ${poseCostumeCount} ${poseFighterName} portraits? Costumes without this pose will be rendered and the renders added to the vault.`)
          : ''}
        confirmText={ap.pendingPose?.isOriginal ? 'Restore' : 'Apply'}
        onConfirm={ap.confirmApplyPose}
        onCancel={() => ap.setPendingPose(null)}
      />

      {cc.removingFighter && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader className="import-loader" size={112} label="Removing character" />
            <h3>Removing {cc.removingFighterName}...</h3>
            <p className="import-status">Please wait...</p>
          </div>
        </div>
      )}

      {cc.batchAddingChars && (
        <div className="import-overlay">
          <div className="import-modal import-modal--hexagon">
            <HexagonLoader
              className="import-loader"
              size={112}
              label="Adding characters"
              progress={cc.batchCharProgress.total > 0 ? (cc.batchCharProgress.current / cc.batchCharProgress.total) * 100 : null}
              minimumVisibleProgress={6}
            />
            <h3>Adding Characters...</h3>
            <p className="import-status">{cc.batchCharProgress.current} / {cc.batchCharProgress.total}</p>
          </div>
        </div>
      )}

      <ConfirmDialog
        show={cm.showConfirmDialog}
        title="Remove Costume"
        message={cm.pendingRemoval
          ? (cm.pendingRemoval.isIceClimbers
              ? `Are you sure you want to remove "${cm.pendingRemoval.costumeName}" (and paired Nana) from Ice Climbers?`
              : `Are you sure you want to remove "${cm.pendingRemoval.costumeName}" from ${cm.pendingRemoval.fighterName}?`)
          : ''}
        confirmText="Remove"
        onConfirm={cm.confirmRemoveCostume}
        onCancel={() => { cm.setShowConfirmDialog(false); cm.setPendingRemoval(null); }}
      />
    </div>
  )
}
