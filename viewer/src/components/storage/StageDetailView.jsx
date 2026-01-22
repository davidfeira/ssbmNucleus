/**
 * StageDetailView - Stage detail with variants
 *
 * Features:
 * - Display stage variants in grid
 * - Drag and drop reordering with smooth animations
 * - Edit, CSP manager, context menu integration
 */

import { useAutoAnimate } from '@formkit/auto-animate/react'
import EditModal from './EditModal'
import CspManagerModal from './CspManagerModal'
import SlippiSafetyDialog from '../shared/SlippiSafetyDialog'
import ContextMenu from './ContextMenu'
import EmbeddedModelViewer from '../EmbeddedModelViewer'

export default function StageDetailView({
  selectedStage,
  stageVariants,
  onBack,
  // Drag and drop
  draggedItem,
  dragOverIndex,
  previewOrder,
  reordering,
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
  handleSaveCspManager,
  // Slippi dialog
  showSlippiDialog,
  slippiDialogData,
  retestingItem,
  handleRetestFixChoice,
  handleSlippiChoice,
  // API
  API_URL
}) {
  const stageInfo = selectedStage
  const variants = stageVariants[selectedStage.code] || []

  // Smooth reorder animations
  const [animateRef] = useAutoAnimate({ duration: 200 })

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        <button
          onClick={onBack}
          className="back-button"
        >
          ← Back to Stages
        </button>

        {variants.length === 0 ? (
          <div className="no-skins-message">
            <p>No stage variants yet. Add some to your storage!</p>
          </div>
        ) : (
          <div className="skins-grid" ref={animateRef}>
            {(previewOrder || variants).map((variant, idx) => {
              const isDragging = draggedItem && variant.id === draggedItem.id
              return (
                <div
                  key={variant.id}
                  className={`skin-card ${isDragging ? 'dragging' : ''}`}
                  draggable={!reordering}
                  onDragStart={(e) => handleDragStart(e, variants.findIndex(v => v.id === variant.id), variants)}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, idx, previewOrder || variants)}
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
                        src={`${API_URL.replace('/api/mex', '')}${variant.screenshotUrl}`}
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
        onSave={handleSaveCspManager}
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
    </div>
  )
}
