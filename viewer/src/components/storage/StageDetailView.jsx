/**
 * StageDetailView - Stage detail with variants
 *
 * Features:
 * - Display stage variants in grid
 * - Drag and drop reordering with smooth animations
 * - Edit, CSP manager, context menu integration
 */

import { useEffect, useState } from 'react'
import { useAutoAnimate } from '@formkit/auto-animate/react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { useFolderManagement } from '../../hooks/useFolderManagement'
import { buildDisplayList, countSkinsInFolder } from '../../utils/storageViewerUtils'
import StageAIStudioModal from './StageAIStudioModal'
import SongPacksModal from './SongPacksModal'
import FolderCard from './FolderCard'
import EditModal from './EditModal'
import CspManagerModal from './CspManagerModal'
import SlippiSafetyDialog from '../shared/SlippiSafetyDialog'
import ConfirmDialog from '../shared/ConfirmDialog'
import ContextMenu from './ContextMenu'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import { useInGameTest } from '../../hooks/useInGameTest'

// Stage variant folders reuse the costume folder UI/hook against the stage
// folder endpoints (see storage_stages.py).
const STAGE_FOLDER_ROUTES = {
  create: '/storage/stage-folders/create',
  rename: '/storage/stage-folders/rename',
  delete: '/storage/stage-folders/delete',
  toggle: '/storage/stage-folders/toggle'
}

export default function StageDetailView({
  selectedStage,
  stageVariants,
  onBack,
  // Folder expansion state (owned by StorageViewer so it persists across nav)
  expandedFolders,
  setExpandedFolders,
  // Drag and drop
  draggedItem,
  dragOverIndex,
  previewOrder,
  reordering,
  isDraggingActive,
  justDroppedId,
  justDraggedRef,
  dragTargetFolder,
  handleDragStart,
  handleDragOver,
  handleDragEnter,
  handleDragLeave,
  handleVariantDrop,
  handleDragEnd,
  // Context menu
  handleVariantContextMenu,
  contextMenu,
  handleMoveToTop,
  handleMoveToBottom,
  // Edit modal
  showEditModal,
  editingItem,
  editName,
  setEditName,
  saving,
  deleting,
  exporting,
  cspPreview,
  stockPreview,
  screenshotPreview,
  lastImageUpdate,
  editSlippiSafe,
  setEditSlippiSafe,
  slippiAdvancedOpen,
  setSlippiAdvancedOpen,
  handleSave,
  handleCancel,
  handleDelete,
  handleExport,
  handleCspChange,
  handleStockChange,
  handleScreenshotChange,
  replaceStageScreenshotWithCapture,
  handleSlippiRetest,
  handleSlippiOverride,
  openCspManager,
  startSkinCreatorFromVault,
  show3DViewer,
  setShow3DViewer,
  handleEditClick,
  // CSP Manager
  showCspManager,
  cspManagerSkin,
  pendingMainCspPreview,
  hdCspInfo,
  compareSliderPosition,
  alternativeCsps,
  capturingHdCsp,
  closeCspManager,
  handleCspManagerMainChange,
  handleCompareSliderStart,
  handleSwapCsp,
  handleRemoveAlternativeCsp,
  handleAddAlternativeCsp,
  handleCaptureHdCsp,
  handleRegenerateAltHd,
  handleSaveCspManager,
  // Slippi dialog
  showSlippiDialog,
  slippiDialogData,
  retestingItem,
  handleRetestFixChoice,
  handleSlippiChoice,
  // Confirm dialog
  showConfirmDialog,
  confirmDialogData,
  confirmDelete,
  cancelDelete,
  // Refresh after AI Studio saves a variant
  onRefresh,
  // Refresh the stage variants list (folder ops change it, not metadata alone)
  onRefreshVariants,
  // API
  API_URL
}) {
  // Folder ops and reorders need the variants list refetched AND metadata
  // refreshed; bundle both so the folder hook and delete handler stay in sync.
  const refreshAll = async () => {
    if (onRefreshVariants) await onRefreshVariants()
    if (onRefresh) await onRefresh()
  }
  const stageInfo = selectedStage
  // `variants` now includes inline folder entries (type:'folder') emitted by the
  // das variants endpoint, in metadata order — same shape as character skins.
  const variants = stageVariants[selectedStage.code] || []
  const variantCount = variants.filter(v => v.type !== 'folder').length

  // Folder management — stage routes, keyed by the stage's storage folder.
  const {
    editingFolderId,
    setEditingFolderId,
    editingFolderName,
    setEditingFolderName,
    toggleFolder,
    handleCreateFolder,
    startEditingFolder,
    saveFolderName
  } = useFolderManagement({
    idField: 'stageFolder',
    idValue: selectedStage.folder,
    routes: STAGE_FOLDER_ROUTES,
    API_URL,
    onRefresh: refreshAll,
    expandedFolders,
    setExpandedFolders
  })

  // Use previewOrder during drag for live reordering visual
  const itemsForDisplay = previewOrder || variants
  const displayList = buildDisplayList(itemsForDisplay, expandedFolders || {})

  const handleDeleteFolder = async (folderId) => {
    try {
      const response = await fetch(`${API_URL}/storage/stage-folders/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageFolder: selectedStage.folder,
          folderId
        })
      })
      const data = await response.json()
      if (data.success) {
        await refreshAll()
      } else {
        alert(`Failed to delete folder: ${data.error}`)
      }
    } catch (err) {
      console.error('Delete folder error:', err)
      alert(`Error deleting folder: ${err.message}`)
    }
  }

  // AI Stage Studio (gated by backend probe + per-stage region map; greyed
  // until setup — an OpenRouter key or a local model — is complete)
  const [aiStages, setAiStages] = useState(null)
  const [aiReady, setAiReady] = useState(true)
  const [showAiStudio, setShowAiStudio] = useState(false)
  useEffect(() => {
    fetch(`${API_URL}/stage-lab/ai-status`)
      .then((r) => r.json())
      .then((d) => {
        setAiStages(d.enabled ? (d.stages || []) : [])
        setAiReady(Boolean(d.hasKey || d.localModelReady
          || localStorage.getItem('openrouter_api_key')))
      })
      .catch(() => setAiStages([]))
  }, [API_URL])
  const aiAvailable = Array.isArray(aiStages) && aiStages.includes(selectedStage.code)

  // In-game test (per stage skin / DAS variant)
  const inGameTest = useInGameTest()

  // Song packs (alternate stage music playlists, installed per project)
  const [showSongPacks, setShowSongPacks] = useState(false)

  // Smooth reorder animations
  const [animateRef] = useAutoAnimate({ duration: 200 })

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        <div className="character-header">
          <button
            onClick={() => { playSound('back'); onBack(); }}
            className="back-button"
          >
            ← Back to Stages
          </button>
          <div className="character-header-actions">
            <button
              className="character-action-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setShowSongPacks(true); }}
              title="Build alternate music playlists for this stage — installed per project"
            >
              🎵 Songs
            </button>
            <button
              className="character-action-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); handleCreateFolder(); }}
            >
              New Folder
            </button>
          </div>
        </div>

        {variantCount === 0 && (
          <div className="no-skins-message">
            <p>No stage variants yet. Add some to your storage!</p>
          </div>
        )}
        <div className={`skins-grid${isDraggingActive ? ' is-dragging' : ''}`} ref={animateRef}>
            {displayList.map((item, idx) => {
              if (item.type === 'folder') {
                const folderId = item.folder.id
                return (
                  <FolderCard
                    key={folderId}
                    folder={item.folder}
                    isExpanded={item.isExpanded}
                    displayIdx={idx}
                    arrayIdx={item.arrayIndex}
                    isDragging={draggedItem && draggedItem.id === folderId}
                    isDropTarget={dragTargetFolder === folderId}
                    isJustDropped={justDroppedId === folderId}
                    isEditing={editingFolderId === folderId}
                    editingFolderName={editingFolderName}
                    folderSkinCount={countSkinsInFolder(folderId, variants)}
                    reordering={reordering}
                    onToggle={toggleFolder}
                    onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                    onDragOver={handleDragOver}
                    onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                    onDragLeave={handleDragLeave}
                    onDrop={handleVariantDrop}
                    onDragEnd={handleDragEnd}
                    onEditingFolderNameChange={setEditingFolderName}
                    onSaveFolderName={saveFolderName}
                    onCancelEdit={() => setEditingFolderId(null)}
                    onStartEditing={startEditingFolder}
                    onDelete={handleDeleteFolder}
                    justDraggedRef={justDraggedRef}
                    itemNoun="variant"
                  />
                )
              }
              const variant = item.skin
              const isDragging = draggedItem && variant.id === draggedItem.id
              return (
                <div
                  key={variant.id}
                  className={`skin-card ${isDragging ? 'dragging' : ''}`}
                  draggable={!reordering}
                  onMouseEnter={playHoverSound}
                  onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === variant.id), itemsForDisplay)}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === variant.id), itemsForDisplay)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleVariantDrop(e)}
                  onDragEnd={handleDragEnd}
                  onContextMenu={(e) => handleVariantContextMenu(e, variant, idx)}
                  style={{ opacity: isDragging ? 0.5 : 1 }}
                >
                <div className="skin-images">
                  <div className="skin-image-container">
                    {variant.hasScreenshot ? (
                      <img
                        src={`${API_URL.replace('/api/mex', '')}${variant.screenshotUrl}?t=${lastImageUpdate}`}
                        alt={variant.name}
                        className="skin-csp"
                        onError={(e) => {
                          e.target.style.display = 'none'
                          e.target.nextSibling.style.display = 'flex'
                        }}
                      />
                    ) : (
                      <div className="skin-placeholder" style={{ display: 'flex' }}>
                        <span className="skin-initial">{variant.name[0]}</span>
                      </div>
                    )}
                    <button
                      className="btn-edit"
                      onClick={(e) => {
                        e.stopPropagation()
                        e.preventDefault()
                        playSound('boop')
                        handleEditClick('stage', {
                          id: variant.id,  // ← Use the immutable ID for API calls
                          name: variant.name,  // ← Use the editable name for display
                          stageCode: stageInfo?.code,
                          stageFolder: stageInfo?.folder,
                          stageName: stageInfo?.name,
                          screenshotUrl: variant.screenshotUrl,
                          hasScreenshot: variant.hasScreenshot,
                          slippi_safe: variant.slippi_safe,
                          slippi_tested: variant.slippi_tested
                        })
                      }}
                      title="Edit variant"
                    >
                      ✎
                    </button>
                  </div>
                </div>

                <div className="skin-info">
                  <div className="skin-color">{variant.name}</div>
                </div>
              </div>
            )
          })}
          {aiAvailable && (
            <div
              className={`create-mod-card ai${aiReady ? '' : ' gated'}`}
              title={aiReady ? undefined
                : 'Set up AI Studio in Settings (OpenRouter key or a local model)'}
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('start'); setShowAiStudio(true); }}
            >
              <div className="create-mod-image-area">
                <span className="create-mod-icon">{aiReady ? '✨' : '🔒'}</span>
              </div>
              <div className="create-mod-info">
                <span className="create-mod-label">AI Stage Studio</span>
              </div>
            </div>
          )}
        </div>
      </div>
      <StageAIStudioModal
        show={showAiStudio}
        stage={selectedStage}
        onClose={() => setShowAiStudio(false)}
        onSaved={onRefresh}
      />
      <SongPacksModal
        show={showSongPacks}
        stage={selectedStage.code}
        displayName={selectedStage.name}
        API_URL={API_URL}
        onClose={() => setShowSongPacks(false)}
      />
      <EditModal
        show={showEditModal}
        editingItem={editingItem}
        editName={editName}
        onNameChange={setEditName}
        saving={saving}
        deleting={deleting}
        exporting={exporting}
        cspPreview={cspPreview}
        stockPreview={stockPreview}
        screenshotPreview={screenshotPreview}
        lastImageUpdate={lastImageUpdate}
        editSlippiSafe={editSlippiSafe}
        onSlippiSafeChange={setEditSlippiSafe}
        slippiAdvancedOpen={slippiAdvancedOpen}
        onSlippiAdvancedToggle={() => setSlippiAdvancedOpen(!slippiAdvancedOpen)}
        onSave={handleSave}
        onCancel={() => { inGameTest.resetTest(); handleCancel(); }}
        onDelete={handleDelete}
        onExport={handleExport}
        onCspChange={handleCspChange}
        onStockChange={handleStockChange}
        onScreenshotChange={handleScreenshotChange}
        onSlippiRetest={handleSlippiRetest}
        onSlippiOverride={handleSlippiOverride}
        onOpenCspManager={openCspManager}
        onStartSkinCreator={startSkinCreatorFromVault}
        onView3D={() => setShow3DViewer(true)}
        onTestInGame={() => inGameTest.startStageSkinTest({
          stageCode: editingItem?.data?.stageCode,
          stageFolder: editingItem?.data?.stageFolder,
          variantId: editingItem?.data?.id,
          name: editingItem?.data?.name
        })}
        onCaptureScreenshot={() => inGameTest.captureStageScreenshot({
          stageCode: editingItem?.data?.stageCode,
          stageFolder: editingItem?.data?.stageFolder,
          variantId: editingItem?.data?.id,
          name: editingItem?.data?.name
        })}
        onReplaceWithCapture={(dataUri) => {
          inGameTest.resetTest()
          replaceStageScreenshotWithCapture(dataUri)
        }}
        testingInGame={inGameTest.testingInGame}
        testStatus={inGameTest.testStatus}
        testResult={inGameTest.testResult}
        testError={inGameTest.testError}
        testMode={inGameTest.testMode}
        onResetTest={inGameTest.resetTest}
        API_URL={API_URL}
      />
      {show3DViewer && editingItem && editingItem.type === 'costume' && (
        <EmbeddedModelViewer
          character={editingItem.data.character}
          skinId={editingItem.data.id}
          onClose={() => setShow3DViewer(false)}
        />
      )}
      <CspManagerModal
        show={showCspManager}
        cspManagerSkin={cspManagerSkin}
        pendingMainCspPreview={pendingMainCspPreview}
        hdCspInfo={hdCspInfo}
        compareSliderPosition={compareSliderPosition}
        lastImageUpdate={lastImageUpdate}
        alternativeCsps={alternativeCsps}
        capturingHdCsp={capturingHdCsp}
        onClose={closeCspManager}
        onCspManagerMainChange={handleCspManagerMainChange}
        onCompareSliderStart={handleCompareSliderStart}
        onSwapCsp={handleSwapCsp}
        onRemoveAlternativeCsp={handleRemoveAlternativeCsp}
        onAddAlternativeCsp={handleAddAlternativeCsp}
        onCaptureHdCsp={handleCaptureHdCsp}
        onRegenerateAltHd={handleRegenerateAltHd}
        onSave={handleSaveCspManager}
        API_URL={API_URL}
      />
      <SlippiSafetyDialog
        show={showSlippiDialog}
        data={slippiDialogData}
        onChoice={retestingItem !== null ? handleRetestFixChoice : handleSlippiChoice}
        isRetest={retestingItem !== null}
      />
      <ConfirmDialog
        show={showConfirmDialog}
        title={confirmDialogData?.title}
        message={confirmDialogData?.message}
        confirmText={confirmDialogData?.confirmText}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />
      <ContextMenu
        contextMenu={contextMenu}
        onMoveToTop={handleMoveToTop}
        onMoveToBottom={handleMoveToBottom}
      />
    </div>
  )
}
