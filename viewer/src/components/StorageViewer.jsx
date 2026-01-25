import { useState, useEffect, useRef, useCallback } from 'react'
import './StorageViewer.css'
import './IsoBuilder.css'
import { DEFAULT_CHARACTERS } from '../defaultCharacters'
import EmbeddedModelViewer from './EmbeddedModelViewer'
import SkinCreator from './SkinCreator'
import SlippiSafetyDialog from './shared/SlippiSafetyDialog'
import ConfirmDialog from './shared/ConfirmDialog'
import EditModal from './storage/EditModal'
import CspManagerModal from './storage/CspManagerModal'
import FolderCard from './storage/FolderCard'
import SkinCard from './storage/SkinCard'
import ContextMenu from './storage/ContextMenu'
import XdeltaImportModal from './storage/XdeltaImportModal'
import XdeltaEditModal from './storage/XdeltaEditModal'
import XdeltaCreateModal from './storage/XdeltaCreateModal'
import XdeltaBuildModal from './storage/XdeltaBuildModal'
import BundleEditModal from './storage/BundleEditModal'
import ModeToolbar from './storage/ModeToolbar'
import ImportToolbar from './storage/ImportToolbar'
import CharactersGrid from './storage/CharactersGrid'
import StagesGrid from './storage/StagesGrid'
import PatchesGrid from './storage/PatchesGrid'
import CharacterDetailView from './storage/CharacterDetailView'
import StageDetailView from './storage/StageDetailView'
import { useDragAndDrop } from '../hooks/useDragAndDrop'
import { useFolderManagement } from '../hooks/useFolderManagement'
import { useFileImport } from '../hooks/useFileImport'
import { useXdeltaPatches } from '../hooks/useXdeltaPatches'
import { useXdeltaProgress } from '../hooks/useXdeltaProgress'
import { useCspManager } from '../hooks/useCspManager'
import { useEditModal } from '../hooks/useEditModal'
import { buildDisplayList, countSkinsInFolder, getFolderIdAtPosition } from '../utils/storageViewerUtils'

const API_URL = 'http://127.0.0.1:5000/api/mex'
const BACKEND_URL = 'http://127.0.0.1:5000'

// Skeleton loading components
const SkeletonCard = () => (
  <div className="character-card skeleton-card">
    <div className="character-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '50%', height: '12px' }}></div>
  </div>
)

const SkeletonSkinCard = () => (
  <div className="skin-card skeleton-card">
    <div className="skin-image-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '60%', margin: '0.5rem auto' }}></div>
  </div>
)

export default function StorageViewer({ metadata, onRefresh, onSkinCreatorChange }) {
  const [mode, setMode] = useState('characters') // 'characters', 'stages', or 'patches'
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCharacter, setSelectedCharacter] = useState(null)
  const [selectedStage, setSelectedStage] = useState(null)
  const [stageVariants, setStageVariants] = useState({})
  const [bundles, setBundles] = useState([])
  const [showBundleEditModal, setShowBundleEditModal] = useState(false)
  const [editingBundle, setEditingBundle] = useState(null)

  // Slippi retest dialog state (for retest from edit modal)
  const [retestingItem, setRetestingItem] = useState(null) // For retest dialog

  const [showSkinCreator, setShowSkinCreator] = useState(false) // Skin creator modal
  const [skinCreatorInitialCostume, setSkinCreatorInitialCostume] = useState(null) // For "edit from vault" flow

  const [contextMenu, setContextMenu] = useState(null) // { x, y, type: 'skin'/'variant', item, index }

  // Fetch stage variants function (defined early for use in drag/drop hook)
  const fetchStageVariants = async () => {
    try {
      const response = await fetch(`${API_URL}/das/storage/variants`)
      const data = await response.json()

      if (data.success) {
        // Group variants by stage
        const grouped = {}
        data.variants.forEach(variant => {
          if (!grouped[variant.stageCode]) {
            grouped[variant.stageCode] = []
          }
          grouped[variant.stageCode].push(variant)
        })
        setStageVariants(grouped)
      }
    } catch (err) {
      console.error('Failed to fetch stage variants:', err)
    }
  }

  // Drag and drop hook
  const {
    draggedItem,
    dragStartIndex,
    dragOverIndex,
    previewOrder,
    reordering,
    dragTargetFolder,
    setDragTargetFolder,
    justDraggedRef,
    isDraggingActive,
    justDroppedId,
    setJustDroppedId,
    handleDragStart,
    handleDragOver,
    handleDragEnter,
    handleDragLeave,
    handleSkinDrop,
    handleVariantDrop,
    handleDragEnd
  } = useDragAndDrop({
    mode,
    selectedCharacter,
    selectedStage,
    API_URL,
    onRefresh,
    fetchStageVariants
  })

  // Folder management hook
  const {
    expandedFolders,
    setExpandedFolders,
    editingFolderId,
    setEditingFolderId,
    editingFolderName,
    setEditingFolderName,
    toggleFolder,
    handleCreateFolder,
    startEditingFolder,
    saveFolderName,
    deleteFolder
  } = useFolderManagement({
    selectedCharacter,
    API_URL,
    onRefresh
  })

  // File import hook
  const {
    importing,
    importMessage,
    showSlippiDialog,
    setShowSlippiDialog,
    slippiDialogData,
    setSlippiDialogData,
    pendingFile,
    setPendingFile,
    handleFileImport,
    handleSlippiChoice
  } = useFileImport({
    mode,
    API_URL,
    onRefresh,
    fetchStageVariants
  })

  // Fetch bundles - defined before hooks that need it as callback
  const fetchBundles = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/bundle/list`)
      const data = await response.json()
      if (data.success) {
        setBundles(data.bundles)
      }
    } catch (err) {
      console.error('Failed to fetch bundles:', err)
    }
  }, [])

  // XDelta patches hook
  const {
    xdeltaPatches,
    showXdeltaImportModal,
    setShowXdeltaImportModal,
    xdeltaImportData,
    setXdeltaImportData,
    importingXdelta,
    showXdeltaEditModal,
    setShowXdeltaEditModal,
    editingXdelta,
    setEditingXdelta,
    showXdeltaBuildModal,
    xdeltaBuildState,
    setXdeltaBuildState,
    xdeltaBuildPatch,
    setXdeltaBuildPatch,
    xdeltaBuildFilename,
    setXdeltaBuildFilename,
    xdeltaBuildError,
    setXdeltaBuildError,
    xdeltaBuildProgress,
    setXdeltaBuildProgress,
    xdeltaBuildMessage,
    setXdeltaBuildMessage,
    showXdeltaCreateModal,
    setShowXdeltaCreateModal,
    xdeltaCreateData,
    setXdeltaCreateData,
    xdeltaCreateState,
    setXdeltaCreateState,
    xdeltaCreateId,
    setXdeltaCreateId,
    xdeltaCreateProgress,
    setXdeltaCreateProgress,
    xdeltaCreateMessage,
    setXdeltaCreateMessage,
    xdeltaCreateError,
    setXdeltaCreateError,
    xdeltaCreateResult,
    setXdeltaCreateResult,
    // Bundle import state
    bundlePreview,
    bundleImporting,
    setBundleImporting,
    bundleImportId,
    setBundleImportId,
    bundleProgress,
    setBundleProgress,
    bundleMessage,
    setBundleMessage,
    bundleComplete,
    setBundleComplete,
    bundleError,
    setBundleError,
    bundleResult,
    setBundleResult,
    // Handlers
    fetchXdeltaPatches,
    handleImportXdelta,
    handleBuildXdeltaIso,
    handleDownloadXdeltaIso,
    closeXdeltaBuildModal,
    handleSelectModdedIso,
    handleStartCreateXdelta,
    closeXdeltaCreateModal,
    handleDownloadPatch,
    handleDeleteXdelta,
    handleEditXdelta,
    handleSaveXdeltaEdit,
    handleUpdateXdeltaImage,
    closeXdeltaImportModal,
    // Bundle handlers
    handleBundlePreview,
    handleBundleImport,
    handleBundleReset
  } = useXdeltaPatches({ API_URL, onBundleImportSuccess: fetchBundles })

  // XDelta progress WebSocket hook
  useXdeltaProgress({
    BACKEND_URL,
    xdeltaBuildPatch,
    setXdeltaBuildProgress,
    setXdeltaBuildMessage,
    setXdeltaBuildFilename,
    setXdeltaBuildState,
    setXdeltaBuildError,
    xdeltaCreateId,
    setXdeltaCreateProgress,
    setXdeltaCreateMessage,
    setXdeltaCreateResult,
    setXdeltaCreateState,
    setXdeltaCreateError,
    fetchXdeltaPatches,
    // Bundle import props
    bundleImportId,
    setBundleProgress,
    setBundleMessage,
    setBundleComplete,
    setBundleResult,
    setBundleImporting,
    setBundleError,
    fetchBundles
  })

  // Ref for setEditingItem - used by CSP manager callback (initialized after useEditModal)
  const setEditingItemRef = useRef(null)

  // CSP manager hook
  const {
    showCspManager,
    setShowCspManager,
    cspManagerSkin,
    setCspManagerSkin,
    alternativeCsps,
    setAlternativeCsps,
    pendingMainCsp,
    setPendingMainCsp,
    pendingMainCspPreview,
    setPendingMainCspPreview,
    hdResolution,
    setHdResolution,
    hdCspInfo,
    setHdCspInfo,
    compareSliderPosition,
    setCompareSliderPosition,
    lastImageUpdate,
    setLastImageUpdate,
    capturingHdCsp,
    openCspManager,
    closeCspManager,
    handleCompareSliderStart,
    handleCspManagerMainChange,
    handleAddAlternativeCsp,
    handleSwapCsp,
    handleRemoveAlternativeCsp,
    handleSaveCspManager,
    handleCaptureHdCsp,
    handleRegenerateAltHd,
    handleResetToOriginal,
    handleUploadMainCsp,
    handleUploadAltCsp
  } = useCspManager({
    API_URL,
    onRefresh,
    onUpdateEditingItemAlts: (updater) => {
      if (setEditingItemRef.current) {
        setEditingItemRef.current(prev => prev ? {
          ...prev,
          data: {
            ...prev.data,
            alternateCsps: typeof updater === 'function'
              ? updater(prev.data.alternateCsps || [])
              : updater
          }
        } : prev)
      }
    },
    onUpdateEditingItemActiveCsp: (activeCspId) => {
      if (setEditingItemRef.current) {
        setEditingItemRef.current(prev => prev ? {
          ...prev,
          data: {
            ...prev.data,
            active_csp_id: activeCspId
          }
        } : prev)
      }
    }
  })

  // Edit modal hook
  const {
    showEditModal,
    setShowEditModal,
    editingItem,
    setEditingItem,
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
    handleSave,
    handleDelete,
    handleExport,
    handleCancel,
    confirmDelete,
    cancelDelete
  } = useEditModal({ API_URL, onRefresh, fetchStageVariants, setLastImageUpdate })

  // Store setEditingItem in ref for CSP manager callback
  setEditingItemRef.current = setEditingItem

  // Fetch stage variants when in stages mode or when metadata changes
  useEffect(() => {
    if (mode === 'stages') {
      fetchStageVariants()
    }
  }, [mode, metadata])

  // Bundle handlers
  const handleDownloadBundle = (bundleId) => {
    const link = document.createElement('a')
    link.href = `${API_URL}/bundle/download/${bundleId}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleEditBundle = (bundle) => {
    setEditingBundle(bundle)
    setShowBundleEditModal(true)
  }

  const handleSaveBundleEdit = async () => {
    if (!editingBundle) return

    try {
      const response = await fetch(`${API_URL}/bundle/update/${editingBundle.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editingBundle.name,
          description: editingBundle.description
        })
      })
      const data = await response.json()
      if (data.success) {
        fetchBundles()
        setShowBundleEditModal(false)
        setEditingBundle(null)
      } else {
        alert(`Failed to save bundle: ${data.error}`)
      }
    } catch (err) {
      alert(`Error saving bundle: ${err.message}`)
    }
  }

  const handleUpdateBundleImage = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !editingBundle) return

    const formData = new FormData()
    formData.append('image', file)

    try {
      const response = await fetch(`${API_URL}/bundle/update-image/${editingBundle.id}`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        setEditingBundle({ ...editingBundle, imageUrl: data.imageUrl })
        fetchBundles()
      } else {
        alert(`Failed to update image: ${data.error}`)
      }
    } catch (err) {
      alert(`Error updating image: ${err.message}`)
    }
  }

  const handleDeleteBundle = async (bundleId) => {
    try {
      const response = await fetch(`${API_URL}/bundle/delete/${bundleId}`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        fetchBundles()
      } else {
        alert(`Failed to delete bundle: ${data.error}`)
      }
    } catch (err) {
      alert(`Error deleting bundle: ${err.message}`)
    }
  }

  const handleInstallBundle = async (bundle) => {
    const slippiPath = localStorage.getItem('slippi_dolphin_path')
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')

    if (!slippiPath) {
      alert('Slippi Dolphin path not set. Please configure it in Settings.')
      return
    }

    if (!vanillaIsoPath) {
      alert('Vanilla ISO path not set. Please configure it in Settings.')
      return
    }

    // Set up progress tracking via the existing bundle import state
    setBundleImporting(true)
    setBundleProgress(0)
    setBundleMessage('Starting install...')
    setBundleError(null)
    setBundleComplete(false)
    setBundleResult(null)

    // Show the import modal for progress display
    setShowXdeltaImportModal(true)

    try {
      const response = await fetch(`${API_URL}/bundle/install/${bundle.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slippiPath,
          vanillaIsoPath
        })
      })

      const data = await response.json()

      if (data.success) {
        setBundleImportId(data.import_id)
      } else {
        setBundleError(data.error)
        setBundleImporting(false)
      }
    } catch (err) {
      setBundleError(`Install error: ${err.message}`)
      setBundleImporting(false)
    }
  }

  // Fetch xdelta patches and bundles when in patches mode
  useEffect(() => {
    if (mode === 'patches') {
      fetchXdeltaPatches()
      fetchBundles()
    }
  }, [mode])

  // Set loading to false when metadata is available
  useEffect(() => {
    if (metadata) {
      setIsLoading(false)
    }
  }, [metadata])

  const handleSlippiRetest = async (autoFix = false) => {
    if (!editingItem || editingItem.type !== 'costume') return

    try {
      const response = await fetch(`${API_URL}/storage/costumes/retest-slippi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id,
          autoFix: autoFix
        })
      })
      const data = await response.json()

      if (data.success) {
        // If not safe and not auto-fixing, show dialog
        if (!data.slippi_safe && !autoFix) {
          setRetestingItem(editingItem.data)
          setSlippiDialogData({
            unsafe_costumes: [{
              character: editingItem.data.character,
              color: editingItem.data.color
            }]
          })
          setShowSlippiDialog(true)
        } else {
          // Safe or just fixed - reload
          alert(data.message)
          window.location.reload()
        }
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  const handleRetestFixChoice = (choice) => {
    setShowSlippiDialog(false)
    if (choice === 'cancel') {
      setRetestingItem(null)
      setSlippiDialogData(null)
      return
    }
    if (choice === 'fix') {
      // Retest with auto-fix
      handleSlippiRetest(true)
    } else if (choice === 'import_as_is') {
      // Just reload to keep current status
      window.location.reload()
    }
    setRetestingItem(null)
  }

  const handleSlippiOverride = async () => {
    if (!editingItem || editingItem.type !== 'costume') return

    const currentStatus = editingItem.data.slippi_safe
    const newStatus = !currentStatus

    try {
      const response = await fetch(`${API_URL}/storage/costumes/override-slippi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id,
          slippiSafe: newStatus
        })
      })
      const data = await response.json()

      if (data.success) {
        alert(data.message)
        window.location.reload()
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }


  const handleDropOnFolder = async (e, folderId) => {
    e.preventDefault()
    e.stopPropagation()

    if (!draggedItem) return

    setReordering(true)

    try {
      const response = await fetch(`${API_URL}/storage/items/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          itemId: draggedItem.id,
          itemType: draggedItem.type || 'skin',
          targetFolderId: folderId,
          targetIndex: -1 // Append at end
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
      } else {
        alert(`Move to folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Move to folder error:', err)
      alert(`Move to folder error: ${err.message}`)
    } finally {
      setReordering(false)
      setDraggedItem(null)
      setDragStartIndex(null)
      setDragOverIndex(null)
      setPreviewOrder(null)
      setDragTargetFolder(null)
    }
  }

  const handleItemReorder = async (fromIndex, toIndex, parentFolderId = null) => {
    if (fromIndex === toIndex) return

    setReordering(true)

    try {
      const response = await fetch(`${API_URL}/storage/items/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          parentFolderId,
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
    } finally {
      setReordering(false)
    }
  }

  // Context menu handlers
  const handleSkinContextMenu = (e, skin, index) => {
    e.preventDefault()
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      type: 'skin',
      item: skin,
      index
    })
  }

  const handleVariantContextMenu = (e, variant, index) => {
    e.preventDefault()
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      type: 'variant',
      item: variant,
      index
    })
  }

  const handleMoveToTop = async () => {
    if (!contextMenu) return

    setReordering(true)

    try {
      const endpoint = contextMenu.type === 'skin'
        ? `${API_URL}/storage/costumes/move-to-top`
        : `${API_URL}/storage/stages/move-to-top`

      const body = contextMenu.type === 'skin'
        ? {
            character: selectedCharacter,
            skinId: contextMenu.item.id
          }
        : {
            stageFolder: selectedStage.folder,
            variantId: contextMenu.item.id
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Refresh data
        if (contextMenu.type === 'skin') {
          await onRefresh()
        } else {
          await fetchStageVariants()
          await onRefresh()
        }
      } else {
        alert(`Move to top failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Move to top error:', err)
      alert(`Move to top error: ${err.message}`)
    } finally {
      setReordering(false)
      setContextMenu(null)
    }
  }

  const handleMoveToBottom = async () => {
    if (!contextMenu) return

    setReordering(true)

    try {
      const endpoint = contextMenu.type === 'skin'
        ? `${API_URL}/storage/costumes/move-to-bottom`
        : `${API_URL}/storage/stages/move-to-bottom`

      const body = contextMenu.type === 'skin'
        ? {
            character: selectedCharacter,
            skinId: contextMenu.item.id
          }
        : {
            stageFolder: selectedStage.folder,
            variantId: contextMenu.item.id
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Refresh data
        if (contextMenu.type === 'skin') {
          await onRefresh()
        } else {
          await fetchStageVariants()
          await onRefresh()
        }
      } else {
        alert(`Move to bottom failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Move to bottom error:', err)
      alert(`Move to bottom error: ${err.message}`)
    } finally {
      setReordering(false)
      setContextMenu(null)
    }
  }

  const closeContextMenu = () => {
    setContextMenu(null)
  }

  // Click-outside listener for context menu
  useEffect(() => {
    if (contextMenu) {
      const handleClick = () => closeContextMenu()
      document.addEventListener('click', handleClick)
      return () => document.removeEventListener('click', handleClick)
    }
  }, [contextMenu])

  // Merge default characters with metadata
  // Always show all 26 vanilla characters, even if they don't have custom skins
  const allCharacters = { ...metadata?.characters }

  // Add any missing default characters with 0 skins
  Object.keys(DEFAULT_CHARACTERS).forEach(charName => {
    if (!allCharacters[charName]) {
      allCharacters[charName] = { skins: [] }
    }
  })

  const characters = Object.keys(allCharacters).sort()

  // Skin Creator - Open fresh
  const openSkinCreator = () => {
    setSkinCreatorInitialCostume(null)
    setShowSkinCreator(true)
  }

  // Skin Creator - Edit existing costume from vault
  const startSkinCreatorFromVault = (costume) => {
    setShowEditModal(false) // Close edit modal if open
    setSkinCreatorInitialCostume(costume)
    setShowSkinCreator(true)
  }

  // Skin Creator - Close handler
  const closeSkinCreator = () => {
    setShowSkinCreator(false)
    setSkinCreatorInitialCostume(null)
  }




  // If a stage is selected, show its variants
  if (selectedStage) {
    return (
      <StageDetailView
        selectedStage={selectedStage}
        stageVariants={stageVariants}
        onBack={() => setSelectedStage(null)}
        // Drag and drop
        draggedItem={draggedItem}
        dragOverIndex={dragOverIndex}
        previewOrder={previewOrder}
        reordering={reordering}
        handleDragStart={handleDragStart}
        handleDragOver={handleDragOver}
        handleDragEnter={handleDragEnter}
        handleDragLeave={handleDragLeave}
        handleVariantDrop={handleVariantDrop}
        handleDragEnd={handleDragEnd}
        // Context menu
        handleVariantContextMenu={handleVariantContextMenu}
        contextMenu={contextMenu}
        handleMoveToTop={handleMoveToTop}
        handleMoveToBottom={handleMoveToBottom}
        // Edit modal
        showEditModal={showEditModal}
        editingItem={editingItem}
        editName={editName}
        setEditName={setEditName}
        saving={saving}
        deleting={deleting}
        exporting={exporting}
        cspPreview={cspPreview}
        stockPreview={stockPreview}
        screenshotPreview={screenshotPreview}
        lastImageUpdate={lastImageUpdate}
        editSlippiSafe={editSlippiSafe}
        setEditSlippiSafe={setEditSlippiSafe}
        slippiAdvancedOpen={slippiAdvancedOpen}
        setSlippiAdvancedOpen={setSlippiAdvancedOpen}
        handleSave={handleSave}
        handleCancel={handleCancel}
        handleDelete={handleDelete}
        handleExport={handleExport}
        handleCspChange={handleCspChange}
        handleStockChange={handleStockChange}
        handleScreenshotChange={handleScreenshotChange}
        handleSlippiRetest={handleSlippiRetest}
        handleSlippiOverride={handleSlippiOverride}
        openCspManager={openCspManager}
        startSkinCreatorFromVault={startSkinCreatorFromVault}
        show3DViewer={show3DViewer}
        setShow3DViewer={setShow3DViewer}
        handleEditClick={handleEditClick}
        // CSP Manager
        showCspManager={showCspManager}
        cspManagerSkin={cspManagerSkin}
        pendingMainCspPreview={pendingMainCspPreview}
        hdCspInfo={hdCspInfo}
        compareSliderPosition={compareSliderPosition}
        alternativeCsps={alternativeCsps}
        hdResolution={hdResolution}
        capturingHdCsp={capturingHdCsp}
        closeCspManager={closeCspManager}
        handleCspManagerMainChange={handleCspManagerMainChange}
        handleCompareSliderStart={handleCompareSliderStart}
        handleSwapCsp={handleSwapCsp}
        handleRemoveAlternativeCsp={handleRemoveAlternativeCsp}
        handleAddAlternativeCsp={handleAddAlternativeCsp}
        setHdResolution={setHdResolution}
        handleCaptureHdCsp={handleCaptureHdCsp}
        handleRegenerateAltHd={handleRegenerateAltHd}
        handleResetToOriginal={handleResetToOriginal}
        handleSaveCspManager={handleSaveCspManager}
        handleUploadMainCsp={handleUploadMainCsp}
        handleUploadAltCsp={handleUploadAltCsp}
        // Slippi dialog
        showSlippiDialog={showSlippiDialog}
        slippiDialogData={slippiDialogData}
        retestingItem={retestingItem}
        handleRetestFixChoice={handleRetestFixChoice}
        handleSlippiChoice={handleSlippiChoice}
        // Confirm dialog
        showConfirmDialog={showConfirmDialog}
        confirmDialogData={confirmDialogData}
        confirmDelete={confirmDelete}
        cancelDelete={cancelDelete}
        // API
        API_URL={API_URL}
      />
    )
  }

  // If a character is selected, show their skins
  if (selectedCharacter) {
    return (
      <CharacterDetailView
        selectedCharacter={selectedCharacter}
        allCharacters={allCharacters}
        onBack={() => setSelectedCharacter(null)}
        // Drag and drop
        draggedItem={draggedItem}
        dragStartIndex={dragStartIndex}
        dragOverIndex={dragOverIndex}
        previewOrder={previewOrder}
        reordering={reordering}
        isDraggingActive={isDraggingActive}
        justDroppedId={justDroppedId}
        setJustDroppedId={setJustDroppedId}
        handleDragStart={handleDragStart}
        handleDragOver={handleDragOver}
        handleDragEnter={handleDragEnter}
        handleDragLeave={handleDragLeave}
        handleDragEnd={handleDragEnd}
        handleSkinDrop={handleSkinDrop}
        justDraggedRef={justDraggedRef}
        // Folder management
        handleCreateFolder={handleCreateFolder}
        expandedFolders={expandedFolders}
        toggleFolder={toggleFolder}
        editingFolderId={editingFolderId}
        setEditingFolderId={setEditingFolderId}
        editingFolderName={editingFolderName}
        setEditingFolderName={setEditingFolderName}
        saveFolderName={saveFolderName}
        startEditingFolder={startEditingFolder}
        deleteFolder={deleteFolder}
        // Edit modal
        showEditModal={showEditModal}
        editingItem={editingItem}
        editName={editName}
        setEditName={setEditName}
        saving={saving}
        deleting={deleting}
        exporting={exporting}
        cspPreview={cspPreview}
        stockPreview={stockPreview}
        screenshotPreview={screenshotPreview}
        lastImageUpdate={lastImageUpdate}
        editSlippiSafe={editSlippiSafe}
        setEditSlippiSafe={setEditSlippiSafe}
        slippiAdvancedOpen={slippiAdvancedOpen}
        setSlippiAdvancedOpen={setSlippiAdvancedOpen}
        handleSave={handleSave}
        handleCancel={handleCancel}
        handleDelete={handleDelete}
        handleExport={handleExport}
        handleCspChange={handleCspChange}
        handleStockChange={handleStockChange}
        handleScreenshotChange={handleScreenshotChange}
        handleSlippiRetest={handleSlippiRetest}
        handleSlippiOverride={handleSlippiOverride}
        openCspManager={openCspManager}
        startSkinCreatorFromVault={startSkinCreatorFromVault}
        show3DViewer={show3DViewer}
        setShow3DViewer={setShow3DViewer}
        // CSP Manager
        showCspManager={showCspManager}
        cspManagerSkin={cspManagerSkin}
        pendingMainCspPreview={pendingMainCspPreview}
        hdCspInfo={hdCspInfo}
        compareSliderPosition={compareSliderPosition}
        alternativeCsps={alternativeCsps}
        hdResolution={hdResolution}
        capturingHdCsp={capturingHdCsp}
        closeCspManager={closeCspManager}
        handleCspManagerMainChange={handleCspManagerMainChange}
        handleCompareSliderStart={handleCompareSliderStart}
        handleSwapCsp={handleSwapCsp}
        handleRemoveAlternativeCsp={handleRemoveAlternativeCsp}
        handleAddAlternativeCsp={handleAddAlternativeCsp}
        setHdResolution={setHdResolution}
        handleCaptureHdCsp={handleCaptureHdCsp}
        handleRegenerateAltHd={handleRegenerateAltHd}
        handleResetToOriginal={handleResetToOriginal}
        handleSaveCspManager={handleSaveCspManager}
        handleUploadMainCsp={handleUploadMainCsp}
        handleUploadAltCsp={handleUploadAltCsp}
        // Slippi dialog
        showSlippiDialog={showSlippiDialog}
        slippiDialogData={slippiDialogData}
        retestingItem={retestingItem}
        handleRetestFixChoice={handleRetestFixChoice}
        handleSlippiChoice={handleSlippiChoice}
        // Confirm dialog
        showConfirmDialog={showConfirmDialog}
        confirmDialogData={confirmDialogData}
        confirmDelete={confirmDelete}
        cancelDelete={cancelDelete}
        // Context menu
        contextMenu={contextMenu}
        handleMoveToTop={handleMoveToTop}
        handleMoveToBottom={handleMoveToBottom}
        handleSkinContextMenu={handleSkinContextMenu}
        handleEditClick={handleEditClick}
        // Skin creator
        showSkinCreator={showSkinCreator}
        closeSkinCreator={closeSkinCreator}
        openSkinCreator={openSkinCreator}
        onSkinCreatorChange={onSkinCreatorChange}
        onRefresh={onRefresh}
        skinCreatorInitialCostume={skinCreatorInitialCostume}
        // API
        API_URL={API_URL}
      />
    )
  }

  // Character or Stage selection grid
  return (
    <div className="storage-viewer">
      <ModeToolbar
        mode={mode}
        onModeChange={(newMode) => {
          setMode(newMode)
          if (newMode === 'characters') {
            setSelectedStage(null)
          } else if (newMode === 'stages') {
            setSelectedCharacter(null)
          } else if (newMode === 'patches') {
            setSelectedCharacter(null)
            setSelectedStage(null)
          }
        }}
      />

      <ImportToolbar
        mode={mode}
        importing={importing}
        importMessage={importMessage}
        onFileImport={handleFileImport}
        onShowXdeltaImportModal={() => setShowXdeltaImportModal(true)}
      />

      {mode === 'characters' ? (
        <CharactersGrid
          characters={characters}
          allCharacters={allCharacters}
          isLoading={isLoading}
          onSelectCharacter={setSelectedCharacter}
        />
      ) : mode === 'stages' ? (
        <StagesGrid
          stageVariants={stageVariants}
          isLoading={isLoading}
          onSelectStage={setSelectedStage}
        />
      ) : (
        <PatchesGrid
          xdeltaPatches={xdeltaPatches}
          bundles={bundles}
          onEditPatch={handleEditXdelta}
          onDownloadPatch={handleDownloadPatch}
          onBuildIso={handleBuildXdeltaIso}
          onShowCreateModal={() => setShowXdeltaCreateModal(true)}
          onEditBundle={handleEditBundle}
          onDownloadBundle={handleDownloadBundle}
          onInstallBundle={handleInstallBundle}
        />
      )}

      {/* XDelta Import Modal */}
      <XdeltaImportModal
        show={showXdeltaImportModal}
        importData={xdeltaImportData}
        onImportDataChange={setXdeltaImportData}
        importing={importingXdelta}
        onImport={handleImportXdelta}
        onCancel={closeXdeltaImportModal}
        // Bundle props
        bundlePreview={bundlePreview}
        bundleImporting={bundleImporting}
        bundleProgress={bundleProgress}
        bundleMessage={bundleMessage}
        bundleComplete={bundleComplete}
        bundleError={bundleError}
        bundleResult={bundleResult}
        onBundleImport={handleBundleImport}
        onBundlePreview={handleBundlePreview}
        onBundleReset={handleBundleReset}
      />

      {/* XDelta Edit Modal */}
      <XdeltaEditModal
        show={showXdeltaEditModal}
        patch={editingXdelta}
        onPatchChange={setEditingXdelta}
        onSave={handleSaveXdeltaEdit}
        onCancel={() => {
          setShowXdeltaEditModal(false)
          setEditingXdelta(null)
        }}
        onDelete={handleDeleteXdelta}
        onUpdateImage={handleUpdateXdeltaImage}
        BACKEND_URL={BACKEND_URL}
      />

      {/* Bundle Edit Modal */}
      <BundleEditModal
        show={showBundleEditModal}
        bundle={editingBundle}
        onBundleChange={setEditingBundle}
        onSave={handleSaveBundleEdit}
        onCancel={() => {
          setShowBundleEditModal(false)
          setEditingBundle(null)
        }}
        onDelete={handleDeleteBundle}
        onUpdateImage={handleUpdateBundleImage}
        BACKEND_URL={BACKEND_URL}
      />

      {/* XDelta Create Patch Modal */}
      <XdeltaCreateModal
        show={showXdeltaCreateModal}
        xdeltaCreateState={xdeltaCreateState}
        xdeltaCreateData={xdeltaCreateData}
        setXdeltaCreateData={setXdeltaCreateData}
        xdeltaCreateMessage={xdeltaCreateMessage}
        xdeltaCreateError={xdeltaCreateError}
        xdeltaCreateResult={xdeltaCreateResult}
        onClose={closeXdeltaCreateModal}
        onSelectModdedIso={handleSelectModdedIso}
        onStartCreate={handleStartCreateXdelta}
        onDownloadPatch={handleDownloadPatch}
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

      {/* XDelta Build Modal */}
      <XdeltaBuildModal
        show={showXdeltaBuildModal}
        xdeltaBuildState={xdeltaBuildState}
        xdeltaBuildPatch={xdeltaBuildPatch}
        xdeltaBuildProgress={xdeltaBuildProgress}
        xdeltaBuildMessage={xdeltaBuildMessage}
        xdeltaBuildFilename={xdeltaBuildFilename}
        xdeltaBuildError={xdeltaBuildError}
        onClose={closeXdeltaBuildModal}
        onDownload={handleDownloadXdeltaIso}
      />
    </div>
  )
}

