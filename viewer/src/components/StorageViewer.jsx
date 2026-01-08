import { useState, useEffect } from 'react'
import './StorageViewer.css'
import './IsoBuilder.css'
import { DEFAULT_CHARACTERS } from '../defaultCharacters'
import EmbeddedModelViewer from './EmbeddedModelViewer'
import SkinCreator from './SkinCreator'
import SlippiSafetyDialog from './shared/SlippiSafetyDialog'
import EditModal from './storage/EditModal'
import CspManagerModal from './storage/CspManagerModal'
import FolderCard from './storage/FolderCard'
import SkinCard from './storage/SkinCard'
import ContextMenu from './storage/ContextMenu'
import XdeltaImportModal from './storage/XdeltaImportModal'
import XdeltaEditModal from './storage/XdeltaEditModal'
import XdeltaCreateModal from './storage/XdeltaCreateModal'
import XdeltaBuildModal from './storage/XdeltaBuildModal'
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

  // Slippi retest dialog state (for retest from edit modal)
  const [retestingItem, setRetestingItem] = useState(null) // For retest dialog

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState(null) // { type: 'costume'/'stage', data: {...} }
  const [editName, setEditName] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [newScreenshot, setNewScreenshot] = useState(null) // File object for new screenshot
  const [screenshotPreview, setScreenshotPreview] = useState(null) // Preview URL for new screenshot
  const [newCsp, setNewCsp] = useState(null) // File object for new CSP
  const [cspPreview, setCspPreview] = useState(null) // Preview URL for new CSP
  const [newStock, setNewStock] = useState(null) // File object for new stock
  const [stockPreview, setStockPreview] = useState(null) // Preview URL for new stock
  const [editSlippiSafe, setEditSlippiSafe] = useState(null) // Track slippi changes for stages
  const [show3DViewer, setShow3DViewer] = useState(false) // 3D model viewer
  const [slippiAdvancedOpen, setSlippiAdvancedOpen] = useState(false) // Collapsible Slippi controls
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
    handleUpdateXdeltaImage
  } = useXdeltaPatches({ API_URL })

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
    fetchXdeltaPatches
  })

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
    handleCaptureHdCsp
  } = useCspManager({ API_URL, onRefresh })

  // Fetch stage variants when in stages mode or when metadata changes
  useEffect(() => {
    if (mode === 'stages') {
      fetchStageVariants()
    }
  }, [mode, metadata])

  // Fetch xdelta patches when in patches mode
  useEffect(() => {
    if (mode === 'patches') {
      fetchXdeltaPatches()
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

  const handleEditClick = (type, data) => {
    const item = { type, data }
    const name = type === 'costume' ? data.color : data.name
    setEditingItem(item)
    setEditName(name)
    setSaving(false)
    setDeleting(false)
    setNewScreenshot(null)
    setScreenshotPreview(null)
    setNewCsp(null)
    setCspPreview(null)
    setNewStock(null)
    setStockPreview(null)
    setEditSlippiSafe(type === 'stage' ? data.slippi_safe : null)
    setShowEditModal(true)
  }

  const handleScreenshotChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewScreenshot(file)

    // Create preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      setScreenshotPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  const handleCspChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewCsp(file)

    // Create preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      setCspPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  const handleStockChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewStock(file)

    // Create preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      setStockPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  // CSP Manager handlers

  const handleSave = async () => {
    if (!editName.trim()) {
      alert('Name cannot be empty')
      return
    }

    setSaving(true)

    try {
      // Save name change
      const endpoint = editingItem.type === 'costume'
        ? `${API_URL}/storage/costumes/rename`
        : `${API_URL}/storage/stages/rename`

      const body = editingItem.type === 'costume'
        ? {
            character: editingItem.data.character,
            skinId: editingItem.data.id,
            newName: editName
          }
        : {
            stageFolder: editingItem.data.stageFolder,
            variantId: editingItem.data.id,
            newName: editName
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (!data.success) {
        alert(`Save failed: ${data.error}`)
        setSaving(false)
        return
      }

      // If this is a stage and there's a new screenshot, upload it
      if (editingItem.type === 'stage' && newScreenshot) {
        const formData = new FormData()
        formData.append('stageFolder', editingItem.data.stageFolder)
        formData.append('variantId', editingItem.data.id)
        formData.append('screenshot', newScreenshot)

        const screenshotResponse = await fetch(`${API_URL}/storage/stages/update-screenshot`, {
          method: 'POST',
          body: formData
        })

        const screenshotData = await screenshotResponse.json()

        if (!screenshotData.success) {
          alert(`Screenshot upload failed: ${screenshotData.error}`)
          setSaving(false)
          return
        }
      }

      // If this is a stage and slippi status changed, save it
      if (editingItem.type === 'stage' && editSlippiSafe !== editingItem.data.slippi_safe) {
        const slippiResponse = await fetch(`${API_URL}/storage/stages/set-slippi`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stageName: editingItem.data.stageFolder,
            variantId: editingItem.data.id,
            slippiSafe: editSlippiSafe
          })
        })

        const slippiData = await slippiResponse.json()

        if (!slippiData.success) {
          alert(`Slippi status update failed: ${slippiData.error}`)
          setSaving(false)
          return
        }
      }

      // If this is a character costume and there's a new CSP, upload it
      if (editingItem.type === 'costume' && newCsp) {
        const formData = new FormData()
        formData.append('character', editingItem.data.character)
        formData.append('skinId', editingItem.data.id)
        formData.append('csp', newCsp)

        const cspResponse = await fetch(`${API_URL}/storage/costumes/update-csp`, {
          method: 'POST',
          body: formData
        })

        const cspData = await cspResponse.json()

        if (!cspData.success) {
          alert(`CSP upload failed: ${cspData.error}`)
          setSaving(false)
          return
        }
      }

      // If this is a character costume and there's a new stock icon, upload it
      if (editingItem.type === 'costume' && newStock) {
        const formData = new FormData()
        formData.append('character', editingItem.data.character)
        formData.append('skinId', editingItem.data.id)
        formData.append('stock', newStock)

        const stockResponse = await fetch(`${API_URL}/storage/costumes/update-stock`, {
          method: 'POST',
          body: formData
        })

        const stockData = await stockResponse.json()

        if (!stockData.success) {
          alert(`Stock icon upload failed: ${stockData.error}`)
          setSaving(false)
          return
        }
      }

      // Refetch data before closing modal
      if (editingItem.type === 'stage') {
        await fetchStageVariants()
      }

      // Always await metadata refresh for costumes (CSP/stock updates)
      await onRefresh()

      // If we uploaded a CSP or stock, update cache-busting timestamp to force image reload
      if (newCsp || newStock) {
        setLastImageUpdate(Date.now())
      }

      setShowEditModal(false)
      setEditingItem(null)
    } catch (err) {
      alert(`Save error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    const itemName = editingItem.type === 'costume'
      ? `${editingItem.data.character} - ${editingItem.data.color}`
      : editingItem.data.name

    if (!confirm(`Are you sure you want to delete "${itemName}"? This cannot be undone.`)) {
      return
    }

    setDeleting(true)

    try {
      const endpoint = editingItem.type === 'costume'
        ? `${API_URL}/storage/costumes/delete`
        : `${API_URL}/storage/stages/delete`

      const body = editingItem.type === 'costume'
        ? {
            character: editingItem.data.character,
            skinId: editingItem.data.id
          }
        : {
            stageFolder: editingItem.data.stageFolder,
            variantId: editingItem.data.id
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Refetch data before closing modal
        if (editingItem.type === 'stage') {
          await fetchStageVariants()
        }

        // Always await metadata refresh for costumes
        await onRefresh()

        // Update cache-busting timestamp to force image reload after deletion
        if (editingItem.type === 'costume') {
          setLastImageUpdate(Date.now())
        }

        setShowEditModal(false)
        setEditingItem(null)
      } else {
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)

    try {
      const endpoint = editingItem.type === 'costume'
        ? `${API_URL}/storage/costumes/export`
        : `${API_URL}/storage/stages/export`

      const body = editingItem.type === 'costume'
        ? {
            character: editingItem.data.character,
            skinId: editingItem.data.id,
            colorName: editingItem.data.color
          }
        : {
            stageCode: editingItem.data.stageCode,
            stageName: editingItem.data.stageName,
            variantId: editingItem.data.id,
            variantName: editingItem.data.name
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Trigger download
        const downloadUrl = `${API_URL}/export/mod/${data.filename}`
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = data.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        alert(`Export failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Export error: ${err.message}`)
    } finally {
      setExporting(false)
    }
  }

  const handleCancel = () => {
    setShowEditModal(false)
    setEditingItem(null)
    setEditName('')
    setNewScreenshot(null)
    setScreenshotPreview(null)
    setNewCsp(null)
    setCspPreview(null)
    setNewStock(null)
    setStockPreview(null)
    setEditSlippiSafe(null)
  }

  // Folder helper functions
  // Build display list from skins array (which now contains both skins and folders)
  // Folder items are GROUPED right after their folder header when expanded
  const buildDisplayList = (allSkins) => {
    if (!allSkins?.length) return []

    // Build folder info and collect folder items
    const folderItems = {} // folderId -> [items with arrayIndex]
    const folders = [] // folder objects with arrayIndex
    const rootItems = [] // items not in any folder

    for (let i = 0; i < allSkins.length; i++) {
      const item = allSkins[i]

      if (item.type === 'folder') {
        folders.push({ folder: item, arrayIndex: i })
        folderItems[item.id] = []
      } else if (item.visible !== false) {
        if (item.folder_id) {
          if (!folderItems[item.folder_id]) {
            folderItems[item.folder_id] = []
          }
          folderItems[item.folder_id].push({ skin: item, arrayIndex: i })
        } else {
          rootItems.push({ skin: item, arrayIndex: i })
        }
      }
    }

    // Build display list: root items first, then folders with their items
    const result = []

    // Add root items that come before all folders
    // We need to maintain relative order, so track what we've added
    const addedIndices = new Set()

    // Go through array in order to maintain relative positioning
    for (let i = 0; i < allSkins.length; i++) {
      const item = allSkins[i]

      if (item.type === 'folder') {
        const isExpanded = expandedFolders[item.id] ?? item.expanded ?? true
        result.push({ type: 'folder', folder: item, isExpanded, arrayIndex: i })
        addedIndices.add(i)

        // If expanded, add all items belonging to this folder right after it
        if (isExpanded && folderItems[item.id]) {
          for (const folderItem of folderItems[item.id]) {
            result.push({ type: 'skin', skin: folderItem.skin, folderId: item.id, arrayIndex: folderItem.arrayIndex })
            addedIndices.add(folderItem.arrayIndex)
          }
        }
      } else if (item.visible !== false && !item.folder_id) {
        // Root item - add it
        result.push({ type: 'skin', skin: item, folderId: null, arrayIndex: i })
        addedIndices.add(i)
      }
      // Skip folder items here - they're added after their folder
    }

    return result
  }

  // Count skins in a folder (by folder_id)
  const countSkinsInFolder = (folderId, allSkins) => {
    return allSkins.filter(s => s.folder_id === folderId && s.visible !== false).length
  }

  // Determine folder membership based on position after reorder
  // Returns the folder_id the item should have at the given position
  const getFolderIdAtPosition = (allSkins, position) => {
    // Look backwards from position to find the context
    // If we find a skin with folder_id before hitting a folder or start, we're in that folder
    // If we find a folder, we're right after it (in that folder)
    // If we hit start or a skin without folder_id, we're at root
    for (let i = position - 1; i >= 0; i--) {
      const item = allSkins[i]
      if (item.type === 'folder') {
        // We're right after a folder - in that folder
        return item.id
      }
      if (item.folder_id) {
        // Previous item is in a folder - we're in that folder too
        return item.folder_id
      }
      // Previous item is at root level - we're at root
      return null
    }
    return null // At the start, root level
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
        handleSaveCspManager={handleSaveCspManager}
        // Slippi dialog
        showSlippiDialog={showSlippiDialog}
        slippiDialogData={slippiDialogData}
        retestingItem={retestingItem}
        handleRetestFixChoice={handleRetestFixChoice}
        handleSlippiChoice={handleSlippiChoice}
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
        reordering={reordering}
        handleDragStart={handleDragStart}
        handleDragOver={handleDragOver}
        handleDragEnter={handleDragEnter}
        handleDragLeave={handleDragLeave}
        handleDragEnd={handleDragEnd}
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
        handleSaveCspManager={handleSaveCspManager}
        // Slippi dialog
        showSlippiDialog={showSlippiDialog}
        slippiDialogData={slippiDialogData}
        retestingItem={retestingItem}
        handleRetestFixChoice={handleRetestFixChoice}
        handleSlippiChoice={handleSlippiChoice}
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
          onEditPatch={handleEditXdelta}
          onDownloadPatch={handleDownloadPatch}
          onBuildIso={handleBuildXdeltaIso}
          onShowCreateModal={() => setShowXdeltaCreateModal(true)}
        />
      )}

      {/* XDelta Import Modal */}
      <XdeltaImportModal
        show={showXdeltaImportModal}
        importData={xdeltaImportData}
        onImportDataChange={setXdeltaImportData}
        importing={importingXdelta}
        onImport={handleImportXdelta}
        onCancel={() => {
          setShowXdeltaImportModal(false)
          setXdeltaImportData({ name: '', description: '', file: null, image: null })
        }}
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

