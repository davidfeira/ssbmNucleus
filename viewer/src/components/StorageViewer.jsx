import { useState, useEffect, useRef } from 'react'
import { io } from 'socket.io-client'
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
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')

  // XDelta patches state
  const [xdeltaPatches, setXdeltaPatches] = useState([])
  const [showXdeltaImportModal, setShowXdeltaImportModal] = useState(false)
  const [xdeltaImportData, setXdeltaImportData] = useState({ name: '', description: '', file: null, image: null })
  const [importingXdelta, setImportingXdelta] = useState(false)
  const [showXdeltaEditModal, setShowXdeltaEditModal] = useState(false)
  const [editingXdelta, setEditingXdelta] = useState(null)

  // XDelta build modal state
  const [showXdeltaBuildModal, setShowXdeltaBuildModal] = useState(false)
  const [xdeltaBuildState, setXdeltaBuildState] = useState('idle') // 'idle', 'building', 'complete', 'error'
  const [xdeltaBuildPatch, setXdeltaBuildPatch] = useState(null)
  const [xdeltaBuildFilename, setXdeltaBuildFilename] = useState(null)
  const [xdeltaBuildError, setXdeltaBuildError] = useState(null)
  const [xdeltaBuildProgress, setXdeltaBuildProgress] = useState(0)
  const [xdeltaBuildMessage, setXdeltaBuildMessage] = useState('')
  const socketRef = useRef(null)

  // XDelta create patch state
  const [showXdeltaCreateModal, setShowXdeltaCreateModal] = useState(false)
  const [xdeltaCreateData, setXdeltaCreateData] = useState({ name: '', description: '', moddedIsoPath: '' })
  const [xdeltaCreateState, setXdeltaCreateState] = useState('idle') // 'idle', 'creating', 'complete', 'error'
  const [xdeltaCreateId, setXdeltaCreateId] = useState(null)
  const [xdeltaCreateProgress, setXdeltaCreateProgress] = useState(0)
  const [xdeltaCreateMessage, setXdeltaCreateMessage] = useState('')
  const [xdeltaCreateError, setXdeltaCreateError] = useState(null)
  const [xdeltaCreateResult, setXdeltaCreateResult] = useState(null)

  // Slippi dialog state
  const [showSlippiDialog, setShowSlippiDialog] = useState(false)
  const [slippiDialogData, setSlippiDialogData] = useState(null)
  const [pendingFile, setPendingFile] = useState(null)
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
  const [lastImageUpdate, setLastImageUpdate] = useState(Date.now()) // For cache-busting images
  const [show3DViewer, setShow3DViewer] = useState(false) // 3D model viewer
  const [slippiAdvancedOpen, setSlippiAdvancedOpen] = useState(false) // Collapsible Slippi controls
  const [showSkinCreator, setShowSkinCreator] = useState(false) // Skin creator modal
  const [skinCreatorInitialCostume, setSkinCreatorInitialCostume] = useState(null) // For "edit from vault" flow

  // CSP Manager modal state
  const [showCspManager, setShowCspManager] = useState(false)
  const [cspManagerSkin, setCspManagerSkin] = useState(null) // Current skin being edited
  const [alternativeCsps, setAlternativeCsps] = useState([]) // Array of { id, url, file }
  const [pendingMainCsp, setPendingMainCsp] = useState(null) // New main CSP file pending save
  const [pendingMainCspPreview, setPendingMainCspPreview] = useState(null) // Preview URL
  const [hdResolution, setHdResolution] = useState('4x') // '2x' | '4x' | '8x' | '16x'
  const [hdCspInfo, setHdCspInfo] = useState(null) // { exists: bool, resolution: '4x', size: '1024x1365' }
  const [compareSliderPosition, setCompareSliderPosition] = useState(50) // 0-100% for before/after slider

  const [contextMenu, setContextMenu] = useState(null) // { x, y, type: 'skin'/'variant', item, index }

  // Folder state
  const [expandedFolders, setExpandedFolders] = useState({}) // { folderId: true/false }
  const [editingFolderId, setEditingFolderId] = useState(null)
  const [editingFolderName, setEditingFolderName] = useState('')

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

  // WebSocket connection for xdelta build/create progress
  useEffect(() => {
    const socket = io(BACKEND_URL)
    socketRef.current = socket

    socket.on('connect', () => {
      console.log('Connected to WebSocket for xdelta progress')
    })

    socket.on('xdelta_progress', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildProgress(data.percentage)
        setXdeltaBuildMessage(data.message)
      }
    })

    socket.on('xdelta_complete', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildProgress(100)
        setXdeltaBuildFilename(data.filename)
        setXdeltaBuildState('complete')
      }
    })

    socket.on('xdelta_error', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildError(data.error)
        setXdeltaBuildState('error')
      }
    })

    // XDelta create events
    socket.on('xdelta_create_progress', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateProgress(data.percentage)
        setXdeltaCreateMessage(data.message)
      }
    })

    socket.on('xdelta_create_complete', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateProgress(100)
        setXdeltaCreateResult(data)
        setXdeltaCreateState('complete')
        // Refresh patches list
        fetchXdeltaPatches()
      }
    })

    socket.on('xdelta_create_error', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateError(data.error)
        setXdeltaCreateState('error')
      }
    })

    return () => {
      socket.disconnect()
    }
  }, [xdeltaBuildPatch, xdeltaCreateId])

  const fetchXdeltaPatches = async () => {
    try {
      const response = await fetch(`${API_URL}/xdelta/list`)
      if (!response.ok) {
        console.error('Failed to fetch xdelta patches: Server returned', response.status)
        return
      }
      const text = await response.text()
      if (!text || text.startsWith('<!')) {
        console.error('Failed to fetch xdelta patches: Server returned HTML instead of JSON')
        return
      }
      const data = JSON.parse(text)
      if (data.success) {
        setXdeltaPatches(data.patches)
      }
    } catch (err) {
      console.error('Failed to fetch xdelta patches:', err)
    }
  }

  const handleImportXdelta = async () => {
    if (!xdeltaImportData.file) {
      alert('Please select an xdelta file')
      return
    }

    setImportingXdelta(true)

    try {
      const formData = new FormData()
      formData.append('file', xdeltaImportData.file)
      formData.append('name', xdeltaImportData.name || xdeltaImportData.file.name.replace('.xdelta', ''))
      formData.append('description', xdeltaImportData.description)
      if (xdeltaImportData.image) {
        formData.append('image', xdeltaImportData.image)
      }

      const response = await fetch(`${API_URL}/xdelta/import`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setShowXdeltaImportModal(false)
        setXdeltaImportData({ name: '', description: '', file: null, image: null })
        await fetchXdeltaPatches()
      } else {
        alert(`Import failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Import error: ${err.message}`)
    } finally {
      setImportingXdelta(false)
    }
  }

  const handleBuildXdeltaIso = async (patch) => {
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')

    if (!vanillaIsoPath) {
      alert('No vanilla ISO path set. Please set it in Settings first.')
      return
    }

    // Open modal and set building state
    setXdeltaBuildPatch(patch)
    setXdeltaBuildState('building')
    setXdeltaBuildFilename(null)
    setXdeltaBuildError(null)
    setXdeltaBuildProgress(0)
    setXdeltaBuildMessage('Starting...')
    setShowXdeltaBuildModal(true)

    try {
      const response = await fetch(`${API_URL}/xdelta/build/${patch.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vanillaIsoPath })
      })

      const data = await response.json()

      if (!data.success) {
        setXdeltaBuildError(data.error)
        setXdeltaBuildState('error')
      }
      // If success, we wait for WebSocket events for progress/complete
    } catch (err) {
      setXdeltaBuildError(err.message)
      setXdeltaBuildState('error')
    }
  }

  const handleDownloadXdeltaIso = () => {
    if (!xdeltaBuildFilename) return

    const link = document.createElement('a')
    link.href = `${API_URL}/xdelta/download/${xdeltaBuildFilename}`
    link.download = xdeltaBuildFilename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const closeXdeltaBuildModal = () => {
    setShowXdeltaBuildModal(false)
    setXdeltaBuildState('idle')
    setXdeltaBuildPatch(null)
    setXdeltaBuildFilename(null)
    setXdeltaBuildError(null)
    setXdeltaBuildProgress(0)
    setXdeltaBuildMessage('')
  }

  const handleSelectModdedIso = async () => {
    try {
      // Use Electron's file dialog if available
      if (window.electron?.openIsoDialog) {
        const result = await window.electron.openIsoDialog()
        if (result) {
          setXdeltaCreateData({ ...xdeltaCreateData, moddedIsoPath: result })
        }
      } else {
        alert('File selection requires the desktop app')
      }
    } catch (err) {
      console.error('Failed to select ISO:', err)
    }
  }

  const handleStartCreateXdelta = async () => {
    if (!xdeltaCreateData.moddedIsoPath) {
      alert('Please select a modded ISO file')
      return
    }

    if (!xdeltaCreateData.name.trim()) {
      alert('Please enter a name for the patch')
      return
    }

    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    if (!vanillaIsoPath) {
      alert('No vanilla ISO path set. Please set it in Settings first.')
      return
    }

    // Switch to creating state
    setXdeltaCreateState('creating')
    setXdeltaCreateProgress(0)
    setXdeltaCreateMessage('Starting...')
    setXdeltaCreateError(null)
    setXdeltaCreateResult(null)

    try {
      const response = await fetch(`${API_URL}/xdelta/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vanillaIsoPath,
          moddedIsoPath: xdeltaCreateData.moddedIsoPath,
          name: xdeltaCreateData.name,
          description: xdeltaCreateData.description
        })
      })

      const data = await response.json()

      if (data.success) {
        setXdeltaCreateId(data.create_id)
      } else {
        setXdeltaCreateError(data.error)
        setXdeltaCreateState('error')
      }
    } catch (err) {
      setXdeltaCreateError(err.message)
      setXdeltaCreateState('error')
    }
  }

  const closeXdeltaCreateModal = () => {
    setShowXdeltaCreateModal(false)
    setXdeltaCreateState('idle')
    setXdeltaCreateData({ name: '', description: '', moddedIsoPath: '' })
    setXdeltaCreateId(null)
    setXdeltaCreateProgress(0)
    setXdeltaCreateMessage('')
    setXdeltaCreateError(null)
    setXdeltaCreateResult(null)
  }

  const handleDownloadPatch = (patchId) => {
    const link = document.createElement('a')
    link.href = `${API_URL}/xdelta/download-patch/${patchId}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleDeleteXdelta = async (patchId) => {
    if (!confirm('Are you sure you want to delete this patch?')) return

    try {
      const response = await fetch(`${API_URL}/xdelta/delete/${patchId}`, {
        method: 'POST'
      })

      const data = await response.json()

      if (data.success) {
        await fetchXdeltaPatches()
      } else {
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    }
  }

  const handleEditXdelta = (patch) => {
    setEditingXdelta({ ...patch })
    setShowXdeltaEditModal(true)
  }

  const handleSaveXdeltaEdit = async () => {
    if (!editingXdelta) return

    try {
      const response = await fetch(`${API_URL}/xdelta/update/${editingXdelta.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editingXdelta.name,
          description: editingXdelta.description
        })
      })

      const data = await response.json()

      if (data.success) {
        setShowXdeltaEditModal(false)
        setEditingXdelta(null)
        await fetchXdeltaPatches()
      } else {
        alert(`Save failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Save error: ${err.message}`)
    }
  }

  const handleUpdateXdeltaImage = async (e) => {
    if (!editingXdelta) return

    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('image', file)

    try {
      const response = await fetch(`${API_URL}/xdelta/update-image/${editingXdelta.id}`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setEditingXdelta({ ...editingXdelta, imageUrl: data.imageUrl })
        await fetchXdeltaPatches()
      } else {
        alert(`Image update failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Image update error: ${err.message}`)
    }
  }

  // Track loading state based on metadata
  useEffect(() => {
    if (metadata) {
      // Small delay for smooth transition
      const timer = setTimeout(() => setIsLoading(false), 300)
      return () => clearTimeout(timer)
    }
  }, [metadata])

  const handleFileImport = async (event, slippiAction = null) => {
    const file = slippiAction ? pendingFile : event.target.files[0]
    if (!file) return

    setImporting(true)
    setImportMessage('Uploading and detecting mod type...')

    try {
      const formData = new FormData()
      formData.append('file', file)
      if (slippiAction) {
        formData.append('slippi_action', slippiAction)
      }

      const response = await fetch(`${API_URL}/import/file`, {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()

      // Check if we need to show slippi dialog
      if (data.type === 'slippi_dialog') {
        setSlippiDialogData(data)
        setPendingFile(file)
        setShowSlippiDialog(true)
        setImporting(false)
        setImportMessage('')
        if (event && event.target) event.target.value = null
        return
      }

      if (data.success) {
        const typeMsg = data.type === 'character'
          ? `${data.imported_count} costume(s)`
          : `${data.stage} stage`
        setImportMessage(`✓ Imported ${typeMsg}! Refreshing...`)

        // Refresh metadata
        await onRefresh()

        // If we imported a stage, also refresh stage variants
        if (data.type === 'stage' && mode === 'stages') {
          await fetchStageVariants()
        }

        setImportMessage(`✓ Successfully imported ${typeMsg}!`)
        setTimeout(() => {
          setImporting(false)
          setImportMessage('')
        }, 2000)
      } else {
        setImportMessage(`✗ Import failed: ${data.error}`)
        setTimeout(() => {
          setImporting(false)
          setImportMessage('')
        }, 5000)
      }
    } catch (err) {
      setImportMessage(`✗ Error: ${err.message}`)
      setTimeout(() => {
        setImporting(false)
        setImportMessage('')
      }, 5000)
    }

    // Reset file input
    if (event && event.target) event.target.value = null
  }

  const handleSlippiChoice = (choice) => {
    setShowSlippiDialog(false)
    if (choice === 'cancel') {
      setPendingFile(null)
      setSlippiDialogData(null)
      return
    }
    handleFileImport(null, choice)
  }

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
  const openCspManager = (skinData) => {
    setCspManagerSkin(skinData)
    setAlternativeCsps([])
    setPendingMainCsp(null)
    setPendingMainCspPreview(null)
    setHdResolution('4x')
    setCompareSliderPosition(50) // Reset slider to middle
    if (skinData.has_hd_csp) {
      setHdCspInfo({
        exists: true,
        resolution: skinData.hd_csp_resolution,
        size: skinData.hd_csp_size
      })
    } else {
      setHdCspInfo(null)
    }
    setShowCspManager(true)
  }

  const closeCspManager = () => {
    setShowCspManager(false)
    setCspManagerSkin(null)
    setAlternativeCsps([])
    setPendingMainCsp(null)
    setPendingMainCspPreview(null)
    setCompareSliderPosition(50) // Reset slider position
  }

  const handleCompareSliderStart = (e) => {
    e.preventDefault()
    const handleMove = (moveEvent) => {
      const container = e.target.closest('.csp-manager-main-container')
      if (!container) return
      const rect = container.getBoundingClientRect()
      const x = (moveEvent.clientX || moveEvent.touches?.[0]?.clientX) - rect.left
      const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
      setCompareSliderPosition(percentage)
    }

    const handleEnd = () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.removeEventListener('touchmove', handleMove)
      document.removeEventListener('touchend', handleEnd)
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.addEventListener('touchmove', handleMove)
    document.addEventListener('touchend', handleEnd)
  }

  const handleCspManagerMainChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    setPendingMainCsp(file)
    const reader = new FileReader()
    reader.onload = (e) => setPendingMainCspPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const handleAddAlternativeCsp = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => {
      const newAlt = {
        id: `alt_${Date.now()}`,
        url: ev.target.result,
        file: file
      }
      setAlternativeCsps(prev => [...prev, newAlt])
    }
    reader.readAsDataURL(file)
  }

  const handleSwapCsp = (altIndex) => {
    const altCsp = alternativeCsps[altIndex]
    if (!altCsp) return

    // Get current main CSP info
    const currentMainUrl = pendingMainCspPreview ||
      (cspManagerSkin?.has_csp ? `${cspManagerSkin.cspUrl}?t=${lastImageUpdate}` : null)
    const currentMainFile = pendingMainCsp

    // Swap: alt becomes main, main becomes alt
    setPendingMainCspPreview(altCsp.url)
    setPendingMainCsp(altCsp.file)

    // Update alternatives: replace swapped alt with old main
    setAlternativeCsps(prev => {
      const updated = [...prev]
      if (currentMainUrl) {
        updated[altIndex] = {
          id: `alt_${Date.now()}`,
          url: currentMainUrl,
          file: currentMainFile
        }
      } else {
        // No main CSP existed, just remove the alt
        updated.splice(altIndex, 1)
      }
      return updated
    })
  }

  const handleRemoveAlternativeCsp = (altIndex) => {
    setAlternativeCsps(prev => prev.filter((_, i) => i !== altIndex))
  }

  const handleSaveCspManager = () => {
    // TODO: Implement backend save
    // For now, just close the modal
    closeCspManager()
  }

  const [capturingHdCsp, setCapturingHdCsp] = useState(false)

  const handleCaptureHdCsp = async () => {
    if (!cspManagerSkin) return

    const scaleNum = parseInt(hdResolution.replace('x', ''))
    setCapturingHdCsp(true)

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/capture-hd`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scale: scaleNum })
        }
      )

      const data = await response.json()

      if (data.success) {
        setHdCspInfo({
          exists: true,
          resolution: data.resolution,
          size: data.size
        })
        // Refresh metadata to get updated has_hd_csp flag
        if (onRefresh) {
          onRefresh()
        }
      } else {
        alert(`Failed to capture HD CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error capturing HD CSP: ${err.message}`)
    } finally {
      setCapturingHdCsp(false)
    }
  }

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

  const toggleFolder = async (folderId) => {
    // Update local state immediately for responsive UI
    setExpandedFolders(prev => ({
      ...prev,
      [folderId]: !(prev[folderId] ?? true)
    }))

    // Also persist to backend
    try {
      await fetch(`${API_URL}/storage/folders/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          folderId
        })
      })
    } catch (err) {
      console.error('Toggle folder error:', err)
    }
  }

  const handleCreateFolder = async () => {
    try {
      const response = await fetch(`${API_URL}/storage/folders/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          name: 'New Folder'
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
        // Start editing the new folder name
        setEditingFolderId(data.folder.id)
        setEditingFolderName(data.folder.name)
      } else {
        alert(`Create folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Create folder error:', err)
      alert(`Create folder error: ${err.message}`)
    }
  }

  const startEditingFolder = (folder) => {
    setEditingFolderId(folder.id)
    setEditingFolderName(folder.name)
  }

  const saveFolderName = async (folderId) => {
    if (!editingFolderName.trim()) {
      setEditingFolderId(null)
      return
    }

    try {
      const response = await fetch(`${API_URL}/storage/folders/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          folderId,
          newName: editingFolderName.trim()
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
      } else {
        alert(`Rename folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Rename folder error:', err)
      alert(`Rename folder error: ${err.message}`)
    } finally {
      setEditingFolderId(null)
      setEditingFolderName('')
    }
  }

  const deleteFolder = async (folderId) => {
    if (!confirm('Delete this folder? Contents will be moved out, not deleted.')) {
      return
    }

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
        alert(`Delete folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Delete folder error:', err)
      alert(`Delete folder error: ${err.message}`)
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

