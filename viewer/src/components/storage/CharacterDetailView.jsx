/**
 * CharacterDetailView - Character detail with skins/folders
 *
 * Features:
 * - Display character skins in grid with folder support
 * - Drag and drop reordering
 * - Folder management (create, rename, delete)
 * - Edit, CSP manager, context menu integration
 * - Skin creator integration
 */

import { useState, useEffect } from 'react'
import { useAutoAnimate } from '@formkit/auto-animate/react'
import { useInGameTest } from '../../hooks/useInGameTest'
import { useFolderManagement } from '../../hooks/useFolderManagement'
import { buildDisplayList, countSkinsInFolder } from '../../utils/storageViewerUtils'
import { playSound, playHoverSound } from '../../utils/sounds'
import FolderCard from './FolderCard'
import SkinCard from './SkinCard'
import EditModal from './EditModal'
import CspManagerModal from './CspManagerModal'
import SlippiSafetyDialog from '../shared/SlippiSafetyDialog'
import ConfirmDialog from '../shared/ConfirmDialog'
import ContextMenu from './ContextMenu'
import SkinCreator from '../SkinCreator'
import AIStudioModal from './AIStudioModal'
import AIModelStudioModal from './AIModelStudioModal'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import PoseManagerModal from './PoseManagerModal'
import { getDefaultCostumeCode } from './posemanager/animData'
import SoundPacksModal from './SoundPacksModal'
import ExtrasPageView from './ExtrasPageView'
import { hasExtras } from '../../config/extraTypes'

export default function CharacterDetailView({
  selectedCharacter,
  allCharacters,
  onBack,
  // Folder expansion state — owned by StorageViewer so it persists across
  // character navigation; injected into the colocated useFolderManagement hook
  expandedFolders,
  setExpandedFolders,
  // Shared state clusters — these hooks live in StorageViewer because
  // StageDetailView and grid-level modals consume the same state
  dragDrop,
  editModal,
  cspManager,
  slippiDialog,
  contextMenuApi,
  skinCreator,
  // Identity / data / callbacks
  onSkinCreatorChange,
  onRefresh,
  onCostumesUpdated,
  API_URL
}) {
  // AI Skin Studio (feature-gated by the backend /ai-status probe; greyed
  // until setup — an OpenRouter key or a local model — is complete)
  const [aiStudioEnabled, setAiStudioEnabled] = useState(false)
  const [aiReady, setAiReady] = useState(true)
  const [showAiStudio, setShowAiStudio] = useState(false)
  // AI Model Studio (prompt/mesh -> rigged costume) — gated by its own probe
  const [modelStudioEnabled, setModelStudioEnabled] = useState(false)
  const [showModelStudio, setShowModelStudio] = useState(false)
  useEffect(() => {
    fetch(`${API_URL}/skin-lab/ai-status`)
      .then((r) => r.json())
      .then((d) => {
        setAiStudioEnabled(Boolean(d.enabled))
        setAiReady(Boolean(d.hasKey || d.localModelReady
          || localStorage.getItem('openrouter_api_key')))
      })
      .catch(() => setAiStudioEnabled(false))
    fetch(`${API_URL}/model-lab/status`)
      .then((r) => r.json())
      .then((d) => setModelStudioEnabled(Boolean(d.enabled)))
      .catch(() => setModelStudioEnabled(false))
  }, [API_URL])

  // Drag and drop (shared useDragAndDrop instance)
  const {
    draggedItem,
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
    handleDragEnd,
    handleSkinDrop
  } = dragDrop

  // Edit modal (shared useEditModal instance, incl. confirm dialog state)
  const {
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
    editSlippiSafe,
    setEditSlippiSafe,
    slippiAdvancedOpen,
    setSlippiAdvancedOpen,
    show3DViewer,
    setShow3DViewer,
    showConfirmDialog,
    confirmDialogData,
    handleEditClick,
    handleScreenshotChange,
    handleCspChange,
    handleStockChange,
    handleGenerateStock,
    confirmGeneratedStock,
    discardGeneratedStock,
    pendingGeneratedStock,
    generatingStock,
    handleSave,
    handleDelete,
    handleExport,
    handleCancel,
    confirmDelete,
    cancelDelete
  } = editModal

  // CSP manager (shared useCspManager instance)
  const {
    showCspManager,
    cspManagerSkin,
    pendingMainCspPreview,
    hdCspInfo,
    compareSliderPosition,
    alternativeCsps,
    capturingHdCsp,
    lastImageUpdate,
    openCspManager,
    closeCspManager,
    handleCspManagerMainChange,
    handleCompareSliderStart,
    handleSwapCsp,
    handleRemoveAlternativeCsp,
    handleAddAlternativeCsp,
    handleCaptureHdCsp,
    handleRegenerateAltHd,
    handleResetToOriginal,
    handleSaveCspManager,
    handleUploadMainCsp,
    handleUploadAltCsp
  } = cspManager

  // Slippi safety dialog / retest (shared with import flow at StorageViewer level)
  const {
    showSlippiDialog,
    slippiDialogData,
    retestingItem,
    handleRetestFixChoice,
    handleSlippiChoice,
    handleSlippiRetest,
    handleSlippiOverride
  } = slippiDialog

  // Context menu (state shared with StageDetailView's variant context menu)
  const {
    contextMenu,
    handleSkinContextMenu,
    handleMoveToTop,
    handleMoveToBottom
  } = contextMenuApi

  // Skin creator (state shared with "edit from vault" flow in StageDetailView)
  const {
    showSkinCreator,
    openSkinCreator,
    closeSkinCreator,
    startSkinCreatorFromVault,
    skinCreatorInitialCostume
  } = skinCreator

  // Folder management — exclusive to this view, so the hook lives here.
  // Expansion state is injected from StorageViewer to persist across navigation.
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
    selectedCharacter,
    API_URL,
    onRefresh,
    expandedFolders,
    setExpandedFolders
  })

  const charData = allCharacters[selectedCharacter]
  const allSkins = charData?.skins || []
  const skinCount = allSkins.filter(s => s.type !== 'folder' && s.visible !== false).length
  const hasCharacterExtras = hasExtras(selectedCharacter)
  // Use previewOrder during drag for live reordering visual
  const itemsForDisplay = previewOrder || allSkins
  const displayList = buildDisplayList(itemsForDisplay, expandedFolders)

  // Smooth reorder animations - disable during drag for performance
  const [animateRef, enableAnimations] = useAutoAnimate({ duration: 150 })

  // Disable animations during active drag to avoid lag with many items
  if (isDraggingActive) {
    enableAnimations(false)
  } else {
    enableAnimations(true)
  }

  // In-game test (per costume)
  const inGameTest = useInGameTest()

  // Pose manager state
  const [showPoseManager, setShowPoseManager] = useState(false)

  // Sound pack (vanilla character sound bank) state
  const [showSoundBank, setShowSoundBank] = useState(false)
  const isSharedSoundBank = selectedCharacter === 'Zelda' || selectedCharacter === 'Sheik'

  // Extras page state
  const [showExtrasPage, setShowExtrasPage] = useState(false)

  // Helper to delete a folder
  const handleDeleteFolder = async (folderId) => {
    try {
      const response = await fetch(`${API_URL}/storage/folders/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          folderId
        })
      })

      const data = await response.json()
      if (data.success) {
        await onRefresh()
      } else {
        alert(`Failed to delete folder: ${data.error}`)
      }
    } catch (err) {
      console.error('Delete folder error:', err)
      alert(`Error deleting folder: ${err.message}`)
    }
  }

  // Show extras page if selected
  if (showExtrasPage) {
    return (
      <ExtrasPageView
        character={selectedCharacter}
        onBack={() => setShowExtrasPage(false)}
        onRefresh={onRefresh}
        API_URL={API_URL}
      />
    )
  }

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        <div className="character-header">
          <button
            onClick={() => { playSound('back'); onBack(); }}
            className="back-button"
          >
            &larr; Back to Characters
          </button>
          <div className="character-header-actions">
            <button
              className="character-action-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setShowSoundBank(true); }}
              title="Customize this character's voice and sound effects — installed into every ISO you export"
            >
              🔊 Sounds
            </button>
            <button
              className="character-action-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setShowPoseManager(true); }}
              title="Create and manage CSP / portrait poses for this character's costumes"
            >
              🎭 Poses
            </button>
            {hasCharacterExtras && (
              <button
                className="character-action-button character-action-button--extras"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); setShowExtrasPage(true); }}
              >
                Extras
              </button>
            )}
            <button
              className="character-action-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); handleCreateFolder(); }}
            >
              New Folder
            </button>
          </div>
        </div>

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
                  folderSkinCount={countSkinsInFolder(folderId, allSkins)}
                  reordering={reordering}
                  onToggle={toggleFolder}
                  onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                  onDragLeave={handleDragLeave}
                  onDrop={handleSkinDrop}
                  onDragEnd={handleDragEnd}
                  onEditingFolderNameChange={setEditingFolderName}
                  onSaveFolderName={saveFolderName}
                  onCancelEdit={() => setEditingFolderId(null)}
                  onStartEditing={startEditingFolder}
                  onDelete={handleDeleteFolder}
                  justDraggedRef={justDraggedRef}
                />
              )
            } else {
              const skinId = item.skin.id
              return (
                <SkinCard
                  key={skinId}
                  skin={item.skin}
                  selectedCharacter={selectedCharacter}
                  folderId={item.folderId}
                  displayIdx={idx}
                  arrayIdx={item.arrayIndex}
                  isDragging={draggedItem && skinId === draggedItem.id}
                  isDropTarget={false}
                  isJustDropped={justDroppedId === skinId}
                  reordering={reordering}
                  lastImageUpdate={lastImageUpdate}
                  onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === skinId), itemsForDisplay)}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === skinId), itemsForDisplay)}
                  onDragLeave={handleDragLeave}
                  onDrop={handleSkinDrop}
                  onDragEnd={handleDragEnd}
                  onContextMenu={handleSkinContextMenu}
                  onEditClick={handleEditClick}
                  API_URL={API_URL}
                />
              )
            }
          })}
          <div
            className="create-mod-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); openSkinCreator(); }}
          >
            <div className="create-mod-image-area">
              <span className="create-mod-icon">+</span>
            </div>
            <div className="create-mod-info">
              <span className="create-mod-label">Create New Mod</span>
            </div>
          </div>
        </div>

      </div>
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
        onGenerateStock={handleGenerateStock}
        onConfirmGeneratedStock={confirmGeneratedStock}
        onDiscardGeneratedStock={discardGeneratedStock}
        pendingGeneratedStock={pendingGeneratedStock}
        generatingStock={generatingStock}
        onScreenshotChange={handleScreenshotChange}
        onSlippiRetest={handleSlippiRetest}
        onSlippiOverride={handleSlippiOverride}
        onOpenCspManager={openCspManager}
        onOpenPoseManager={() => { playSound('boop'); setShowPoseManager(true); }}
        onStartSkinCreator={startSkinCreatorFromVault}
        onView3D={() => setShow3DViewer(true)}
        onTestInGame={() => inGameTest.startCostumeTest({
          character: editingItem?.data?.character,
          skinId: editingItem?.data?.id,
          colorName: editingItem?.data?.color
        })}
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
        onResetToOriginal={handleResetToOriginal}
        onOpenPoseManager={() => { playSound('boop'); setShowPoseManager(true); }}
        onSave={handleSaveCspManager}
        onUploadMainCsp={handleUploadMainCsp}
        onUploadAltCsp={handleUploadAltCsp}
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
      <SkinCreator
        isOpen={showSkinCreator}
        onClose={closeSkinCreator}
        selectedCharacter={selectedCharacter}
        onSkinCreatorChange={onSkinCreatorChange}
        onRefresh={onRefresh}
        initialCostume={skinCreatorInitialCostume}
        aiStudioEnabled={aiStudioEnabled}
        aiReady={aiReady}
        onOpenAiStudio={() => { closeSkinCreator(); setShowAiStudio(true) }}
        modelStudioEnabled={modelStudioEnabled}
        onOpenModelStudio={() => { closeSkinCreator(); setShowModelStudio(true) }}
      />
      <AIStudioModal
        show={showAiStudio}
        character={selectedCharacter}
        onClose={() => setShowAiStudio(false)}
        onSaved={onRefresh}
      />
      <AIModelStudioModal
        show={showModelStudio}
        character={selectedCharacter}
        onClose={() => setShowModelStudio(false)}
        onSaved={onRefresh}
      />
      <PoseManagerModal
        show={showPoseManager}
        character={selectedCharacter}
        models={(() => {
          const backendBase = API_URL.replace('/api/mex', '')
          const def = getDefaultCostumeCode(selectedCharacter)
          const list = allSkins
            .filter(s => s.type !== 'folder')
            .map(s => ({
              value: s.id,
              label: s.color || s.id,
              skinId: s.id,
              cspUrl: s.has_csp
                ? `${backendBase}/storage/${selectedCharacter}/${s.csp_filename || `${s.id}_csp.png`}`
                : null,
              stockUrl: s.has_stock ? `${backendBase}/storage/${selectedCharacter}/${s.id}_stc.png` : null
            }))
          return def ? [{ value: '__default__', label: 'Default', costumeCode: def }, ...list] : list
        })()}
        onClose={() => setShowPoseManager(false)}
        onRefresh={onRefresh}
        onCostumesUpdated={onCostumesUpdated}
        API_URL={API_URL}
      />
      <SoundPacksModal
        show={showSoundBank}
        character={selectedCharacter}
        displayName={isSharedSoundBank ? 'Zelda / Sheik' : selectedCharacter}
        API_URL={API_URL}
        onClose={() => setShowSoundBank(false)}
      />
    </div>
  )
}
