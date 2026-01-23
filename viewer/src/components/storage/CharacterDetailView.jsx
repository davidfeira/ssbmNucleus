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

import { useState, useEffect, useRef } from 'react'
import { useAutoAnimate } from '@formkit/auto-animate/react'
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
  dragOverIndex,
  previewOrder,
  reordering,
  isDraggingActive,
  justDroppedId,
  setJustDroppedId,
  handleDragStart,
  handleDragOver,
  handleDragEnter,
  handleDragLeave,
  handleDragEnd,
  handleSkinDrop,
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
  // Confirm dialog
  showConfirmDialog,
  confirmDialogData,
  confirmDelete,
  cancelDelete,
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

  // Pose manager state
  const [showPoseManager, setShowPoseManager] = useState(false)

  // Extras page state
  const [showExtrasPage, setShowExtrasPage] = useState(false)

  // More dropdown menu state
  const [showMoreMenu, setShowMoreMenu] = useState(false)
  const moreMenuRef = useRef(null)

  // Close menu when clicking outside
  useEffect(() => {
    if (!showMoreMenu) return

    const handleClickOutside = (e) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target)) {
        setShowMoreMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showMoreMenu])

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
            ← Back to Characters
          </button>
          <div
            className={`more-dropdown ${hasExtras(selectedCharacter) ? 'has-extras' : ''}`}
            ref={moreMenuRef}
          >
            <button
              className="more-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setShowMoreMenu(!showMoreMenu); }}
            >
              More <span className="more-arrow">▼</span>
            </button>
            {showMoreMenu && (
              <div className="more-menu">
                <button onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); handleCreateFolder(); setShowMoreMenu(false); }}>
                  New Folder
                </button>
                <button onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); setShowPoseManager(true); setShowMoreMenu(false); }}>
                  Poses
                </button>
                {hasExtras(selectedCharacter) && (
                  <button className="extras-item" onMouseEnter={playHoverSound} onClick={() => { playSound('boop'); setShowExtrasPage(true); setShowMoreMenu(false); }}>
                    Extras
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {skinCount === 0 && displayList.filter(d => d.type === 'folder').length === 0 ? (
          <div className="no-skins-message">
            <p>No custom skins yet. Add some using the intake system!</p>
          </div>
        ) : (
          <div className="skins-grid" ref={animateRef}>
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
                    isDropTarget={false}
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
