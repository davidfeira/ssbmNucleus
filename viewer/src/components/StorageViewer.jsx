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
import ModeToolbar from './storage/ModeToolbar'
import ImportToolbar from './storage/ImportToolbar'
import CharactersGrid from './storage/CharactersGrid'
import StagesGrid from './storage/StagesGrid'
import PatchesGrid from './storage/PatchesGrid'
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
    const stageInfo = selectedStage
    const variants = stageVariants[selectedStage.code] || []

    return (
      <div className="storage-viewer">
        <div className="character-detail">
          <button
            onClick={() => setSelectedStage(null)}
            className="back-button"
          >
            ← Back to Stages
          </button>

          <h2>{stageInfo?.name}</h2>
          <p className="skin-count">{variants.length} variant{variants.length !== 1 ? 's' : ''}</p>

          {variants.length === 0 ? (
            <div className="no-skins-message">
              <p>No stage variants yet. Add some to your storage!</p>
            </div>
          ) : (
            <div className="skins-grid">
              {(previewOrder || variants).map((variant, idx) => {
                const isDragging = draggedItem && variant.id === draggedItem.id
                return (
                  <div
                    key={variant.id}
                    className={`skin-card ${isDragging ? 'dragging' : ''}`}
                    draggable={!reordering}
                    onDragStart={(e) => handleDragStart(e, variants.findIndex(v => v.id === variant.id), variants)}
                    onDragOver={handleDragOver}
                    onDragEnter={(e) => handleDragEnter(e, idx, variants)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleVariantDrop(e, idx)}
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

  // If a character is selected, show their skins
  if (selectedCharacter) {
    const charData = allCharacters[selectedCharacter]
    // Get all skins (including folders) from character data
    const allSkins = charData?.skins || []
    // Filter to just actual skins (not folders) for the count
    const skinCount = allSkins.filter(s => s.type !== 'folder' && s.visible !== false).length
    // Build display list (handles folder collapse/expand)
    const displayList = buildDisplayList(allSkins)

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

    // Render a folder card
    // Custom drop handler that converts display index to allSkins index
    const handleItemDrop = async (e, displayIdx) => {
      e.preventDefault()
      if (!draggedItem) return

      const fromIndex = dragStartIndex
      const targetItem = displayList[displayIdx]
      const toIndex = targetItem?.arrayIndex ?? allSkins.length - 1

      if (fromIndex === toIndex || !selectedCharacter) {
        setDraggedItem(null)
        setDragStartIndex(null)
        setDragOverIndex(null)
        setPreviewOrder(null)
        return
      }

      setReordering(true)

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
      } finally {
        setReordering(false)
        setDraggedItem(null)
        setDragStartIndex(null)
        setDragOverIndex(null)
        setPreviewOrder(null)
      }
    }

    // Render a skin card
    return (
      <div className="storage-viewer">
        <div className="character-detail">
          <div className="character-header">
            <button
              onClick={() => setSelectedCharacter(null)}
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
          </div>

          <h2>{selectedCharacter}</h2>
          <p className="skin-count">{skinCount} skin{skinCount !== 1 ? 's' : ''}</p>

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
        <SkinCreator
          isOpen={showSkinCreator}
          onClose={closeSkinCreator}
          selectedCharacter={selectedCharacter}
          onSkinCreatorChange={onSkinCreatorChange}
          onRefresh={onRefresh}
          initialCostume={skinCreatorInitialCostume}
        />
      </div>
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
      {showXdeltaCreateModal && (
        <div className="iso-builder-overlay">
          <div className="iso-builder-modal">
            <div className="modal-header">
              <h2>Create New Patch</h2>
              {xdeltaCreateState !== 'creating' && (
                <button className="close-btn" onClick={closeXdeltaCreateModal}>×</button>
              )}
            </div>

            <div className="modal-body">
              {xdeltaCreateState === 'idle' && (
                <div className="create-patch-form">
                  <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
                    Create a patch by comparing a modded ISO against your vanilla ISO.
                    The patch can then be shared and applied to recreate the modded ISO.
                  </p>

                  <div className="edit-field">
                    <label>Patch Name:</label>
                    <input
                      type="text"
                      value={xdeltaCreateData.name}
                      onChange={(e) => setXdeltaCreateData({ ...xdeltaCreateData, name: e.target.value })}
                      placeholder="My Awesome Mod Pack"
                    />
                  </div>

                  <div className="edit-field">
                    <label>Description (optional):</label>
                    <textarea
                      value={xdeltaCreateData.description}
                      onChange={(e) => setXdeltaCreateData({ ...xdeltaCreateData, description: e.target.value })}
                      placeholder="Describe what's in this patch..."
                      rows={3}
                    />
                  </div>

                  <div className="edit-field">
                    <label>Modded ISO:</label>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <input
                        type="text"
                        value={xdeltaCreateData.moddedIsoPath}
                        onChange={(e) => setXdeltaCreateData({ ...xdeltaCreateData, moddedIsoPath: e.target.value })}
                        placeholder="Select a modded ISO file..."
                        readOnly
                        style={{ flex: 1 }}
                      />
                      <button
                        className="btn-secondary"
                        onClick={handleSelectModdedIso}
                        style={{ whiteSpace: 'nowrap' }}
                      >
                        Browse...
                      </button>
                    </div>
                  </div>

                  <div className="edit-buttons" style={{ marginTop: '1.5rem' }}>
                    <button
                      className="btn-save"
                      onClick={handleStartCreateXdelta}
                      disabled={!xdeltaCreateData.moddedIsoPath || !xdeltaCreateData.name.trim()}
                    >
                      Create Patch
                    </button>
                    <button className="btn-cancel" onClick={closeXdeltaCreateModal}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {xdeltaCreateState === 'creating' && (
                <div className="export-progress" style={{ textAlign: 'center' }}>
                  <div className="export-spinner">
                    <div className="spinner"></div>
                  </div>

                  <h3 style={{ marginTop: '1rem' }}>Creating Patch...</h3>

                  <p className="progress-message">
                    {xdeltaCreateMessage || 'Comparing ISOs...'}
                  </p>
                </div>
              )}

              {xdeltaCreateState === 'complete' && xdeltaCreateResult && (
                <div className="export-complete">
                  <div className="success-icon">✓</div>
                  <h3>Patch Created!</h3>
                  <p>Your patch "{xdeltaCreateResult.name}" has been created.</p>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9em' }}>
                    Size: {xdeltaCreateResult.size_mb} MB
                    {xdeltaCreateResult.size_mb < 25 && (
                      <span style={{ color: 'var(--color-success)', marginLeft: '0.5rem' }}>
                        (Discord-friendly!)
                      </span>
                    )}
                  </p>
                  <div className="complete-actions">
                    <button
                      className="btn-download"
                      onClick={() => handleDownloadPatch(xdeltaCreateResult.patch_id)}
                    >
                      Download Patch
                    </button>
                    <button className="btn-secondary" onClick={closeXdeltaCreateModal}>
                      Close
                    </button>
                  </div>
                </div>
              )}

              {xdeltaCreateState === 'error' && (
                <div className="export-error">
                  <div className="error-icon">✕</div>
                  <h3>Creation Failed</h3>
                  <p className="error-message">{xdeltaCreateError}</p>
                  <button className="btn-secondary" onClick={closeXdeltaCreateModal}>
                    Close
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
        </div>
      )}

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
      {showXdeltaBuildModal && (
        <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Build ISO</h2>
          {xdeltaBuildState !== 'building' && (
            <button className="close-btn" onClick={closeXdeltaBuildModal}>×</button>
          )}
        </div>

        <div className="modal-body">
          {xdeltaBuildState === 'building' && (
            <div className="export-progress">
              <div className="progress-header">
                <h3>Building ISO...</h3>
                <span className="progress-percentage">{xdeltaBuildProgress}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${xdeltaBuildProgress}%` }}
                ></div>
              </div>

              <p className="progress-message">
                {xdeltaBuildMessage || `Applying patch: ${xdeltaBuildPatch?.name}`}
              </p>

              <div className="export-spinner">
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {xdeltaBuildState === 'complete' && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Build Complete!</h3>
              <p>Your patched ISO is ready to download.</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownloadXdeltaIso}>
                  Download {xdeltaBuildFilename}
                </button>
                <button className="btn-secondary" onClick={closeXdeltaBuildModal}>
                  Close
                </button>
              </div>
            </div>
          )}

          {xdeltaBuildState === 'error' && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Build Failed</h3>
              <p className="error-message">{xdeltaBuildError}</p>
              <button className="btn-secondary" onClick={closeXdeltaBuildModal}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
      )}
    </div>
  )
}

