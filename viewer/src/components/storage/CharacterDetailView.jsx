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

import { useState } from 'react'
import { buildDisplayList, countSkinsInFolder } from '../../utils/storageViewerUtils'
import FolderCard from './FolderCard'
import SkinCard from './SkinCard'
import EditModal from './EditModal'
import CspManagerModal from './CspManagerModal'
import SlippiSafetyDialog from '../shared/SlippiSafetyDialog'
import ContextMenu from './ContextMenu'
import SkinCreator from '../SkinCreator'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import PoseManagerModal from './PoseManagerModal'
import ExtrasPageView from './ExtrasPageView'
import { hasExtras } from '../../config/extraTypes'

export default function CharacterDetailView({
  selectedCharacter,
  allCharacters,
  onBack,
  // Drag and drop
  draggedItem,
  dragStartIndex,
  reordering,
  handleDragStart,
  handleDragOver,
  handleDragEnter,
  handleDragLeave,
  handleDragEnd,
  justDraggedRef,
  // Folder management
  handleCreateFolder,
  expandedFolders,
  toggleFolder,
  editingFolderId,
  setEditingFolderId,
  editingFolderName,
  setEditingFolderName,
  saveFolderName,
  startEditingFolder,
  deleteFolder,
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
  handleSlippiRetest,
  handleSlippiOverride,
  openCspManager,
  startSkinCreatorFromVault,
  show3DViewer,
  setShow3DViewer,
  // CSP Manager
  showCspManager,
  cspManagerSkin,
  pendingMainCspPreview,
  hdCspInfo,
  compareSliderPosition,
  alternativeCsps,
  hdResolution,
  capturingHdCsp,
  closeCspManager,
  handleCspManagerMainChange,
  handleCompareSliderStart,
  handleSwapCsp,
  handleRemoveAlternativeCsp,
  handleAddAlternativeCsp,
  setHdResolution,
  handleCaptureHdCsp,
  handleRegenerateAltHd,
  handleResetToOriginal,
  handleSaveCspManager,
  handleUploadMainCsp,
  handleUploadAltCsp,
  // Slippi dialog
  showSlippiDialog,
  slippiDialogData,
  retestingItem,
  handleRetestFixChoice,
  handleSlippiChoice,
  // Context menu
  contextMenu,
  handleMoveToTop,
  handleMoveToBottom,
  handleSkinContextMenu,
  handleEditClick,
  // Skin creator
  showSkinCreator,
  closeSkinCreator,
  openSkinCreator,
  onSkinCreatorChange,
  onRefresh,
  skinCreatorInitialCostume,
  // API
  API_URL
}) {
  const charData = allCharacters[selectedCharacter]
  const allSkins = charData?.skins || []
  const skinCount = allSkins.filter(s => s.type !== 'folder' && s.visible !== false).length
  const displayList = buildDisplayList(allSkins, expandedFolders)

  // Pose manager state
  const [showPoseManager, setShowPoseManager] = useState(false)

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

  // Custom drop handler that converts display index to allSkins index
  const handleItemDrop = async (e, displayIdx) => {
    e.preventDefault()
    if (!draggedItem) return

    const fromIndex = dragStartIndex
    const targetItem = displayList[displayIdx]
    const toIndex = targetItem?.arrayIndex ?? allSkins.length - 1

    if (fromIndex === toIndex || !selectedCharacter) {
      // Would be cleaned up by drag handlers
      return
    }

    try {
      const response = await fetch(`${API_URL}/storage/costumes/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          fromIndex,
          toIndex
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
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
            onClick={onBack}
            className="back-button"
          >
            ← Back to Characters
          </button>
          <button
            onClick={handleCreateFolder}
            className="create-folder-button"
            title="Create new folder"
          >
            + New Folder
          </button>
          <button
            onClick={() => setShowPoseManager(true)}
            className="poses-button"
            title="Manage character poses for CSP generation"
          >
            Poses
          </button>
          {hasExtras(selectedCharacter) && (
            <button
              onClick={() => setShowExtrasPage(true)}
              className="extras-button"
              title="Manage character extras (effects, projectiles, etc.)"
            >
              Extras
            </button>
          )}
        </div>

        {skinCount === 0 && displayList.filter(d => d.type === 'folder').length === 0 ? (
          <div className="no-skins-message">
            <p>No custom skins yet. Add some using the intake system!</p>
          </div>
        ) : (
          <div className="skins-grid">
            {displayList.map((item, idx) => {
              if (item.type === 'folder') {
                return (
                  <FolderCard
                    key={item.folder.id}
                    folder={item.folder}
                    isExpanded={item.isExpanded}
                    displayIdx={idx}
                    arrayIdx={item.arrayIndex}
                    isDragging={draggedItem && draggedItem.id === item.folder.id}
                    isEditing={editingFolderId === item.folder.id}
                    editingFolderName={editingFolderName}
                    folderSkinCount={countSkinsInFolder(item.folder.id, allSkins)}
                    reordering={reordering}
                    onToggle={toggleFolder}
                    onDragStart={(e, arrayIdx) => handleDragStart(e, arrayIdx, allSkins)}
                    onDragOver={handleDragOver}
                    onDragEnter={(e, displayIdx) => handleDragEnter(e, displayIdx, displayList)}
                    onDragLeave={handleDragLeave}
                    onDrop={handleItemDrop}
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
                return (
                  <SkinCard
                    key={item.skin.id}
                    skin={item.skin}
                    selectedCharacter={selectedCharacter}
                    folderId={item.folderId}
                    displayIdx={idx}
                    arrayIdx={item.arrayIndex}
                    isDragging={draggedItem && item.skin.id === draggedItem.id}
                    reordering={reordering}
                    lastImageUpdate={lastImageUpdate}
                    onDragStart={(e, arrayIdx) => handleDragStart(e, arrayIdx, allSkins)}
                    onDragOver={handleDragOver}
                    onDragEnter={(e, displayIdx) => handleDragEnter(e, displayIdx, displayList)}
                    onDragLeave={handleDragLeave}
                    onDrop={handleItemDrop}
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
              onClick={openSkinCreator}
            >
              <div className="create-mod-content">
                <span className="create-mod-icon">+</span>
                <span className="create-mod-label">Create New Mod</span>
              </div>
            </div>
          </div>
        )}
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
        onCancel={handleCancel}
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
        hdResolution={hdResolution}
        capturingHdCsp={capturingHdCsp}
        onClose={closeCspManager}
        onCspManagerMainChange={handleCspManagerMainChange}
        onCompareSliderStart={handleCompareSliderStart}
        onSwapCsp={handleSwapCsp}
        onRemoveAlternativeCsp={handleRemoveAlternativeCsp}
        onAddAlternativeCsp={handleAddAlternativeCsp}
        onHdResolutionChange={setHdResolution}
        onCaptureHdCsp={handleCaptureHdCsp}
        onRegenerateAltHd={handleRegenerateAltHd}
        onResetToOriginal={handleResetToOriginal}
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
      />
      <PoseManagerModal
        show={showPoseManager}
        character={selectedCharacter}
        onClose={() => setShowPoseManager(false)}
        onRefresh={onRefresh}
        API_URL={API_URL}
      />
    </div>
  )
}
