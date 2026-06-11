import { useState, useEffect, useRef, useCallback } from 'react'
import './StorageViewer.css'
import './IsoBuilder.css'
import { DEFAULT_CHARACTERS } from '../defaultCharacters'
import EmbeddedModelViewer from './EmbeddedModelViewer'
import SlippiSafetyDialog from './shared/SlippiSafetyDialog'
import DuplicateImportDialog from './shared/DuplicateImportDialog'
import ConfirmDialog from './shared/ConfirmDialog'
import EditModal from './storage/EditModal'
import XdeltaImportModal from './storage/XdeltaImportModal'
import IsoScanModal from './storage/IsoScanModal'
import XdeltaEditModal from './storage/XdeltaEditModal'
import XdeltaCreateModal from './storage/XdeltaCreateModal'
import XdeltaBuildModal from './storage/XdeltaBuildModal'
import BundleEditModal from './storage/BundleEditModal'
import ModeToolbar from './storage/ModeToolbar'
import ImportToolbar from './storage/ImportToolbar'
import CharactersGrid from './storage/CharactersGrid'
import StagesGrid from './storage/StagesGrid'
import BulkStageCaptureModal from './storage/BulkStageCaptureModal'
import PatchesGrid from './storage/PatchesGrid'
import MenusGrid from './storage/MenusGrid'
import CssMenuTypesGrid from './storage/CssMenuTypesGrid'
import SssMenuTypesGrid from './storage/SssMenuTypesGrid'
import IconGridModsView from './storage/IconGridModsView'
import BackgroundModsView from './storage/BackgroundModsView'
import DoorModsView from './storage/DoorModsView'
import PauseModsView from './storage/PauseModsView'
import SssLayoutEditor from './storage/SssLayoutEditor'
import CharacterDetailView from './storage/CharacterDetailView'
import StageDetailView from './storage/StageDetailView'
import CustomStagesGrid from './storage/CustomStagesGrid'
import CustomStageDetailView from './storage/CustomStageDetailView'
import CustomCharactersGrid from './storage/CustomCharactersGrid'
import CustomCharacterDetailView from './storage/CustomCharacterDetailView'
import { useDragAndDrop } from '../hooks/useDragAndDrop'
import { useFileImport } from '../hooks/useFileImport'
import { useXdeltaPatches } from '../hooks/useXdeltaPatches'
import { useXdeltaProgress } from '../hooks/useXdeltaProgress'
import { useCspManager } from '../hooks/useCspManager'
import { useEditModal } from '../hooks/useEditModal'
import { playSound, playHoverSound } from '../utils/sounds'
import { API_URL, BACKEND_URL } from '../config'

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
  const [mode, setMode] = useState('characters') // 'characters', 'stages', 'patches', or 'menus'
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCharacter, setSelectedCharacter] = useState(null)
  const [selectedStage, setSelectedStage] = useState(null)
  const [selectedMenuType, setSelectedMenuType] = useState(null) // 'css' or 'sss'
  const [selectedMenuModType, setSelectedMenuModType] = useState(null) // e.g. 'icon_grid'
  const [menuDetailOpen, setMenuDetailOpen] = useState(false)
  const [stageVariants, setStageVariants] = useState({})
  const [showBulkCapture, setShowBulkCapture] = useState(false)
  const [bundles, setBundles] = useState([])
  const [showBundleEditModal, setShowBundleEditModal] = useState(false)
  const [editingBundle, setEditingBundle] = useState(null)

  // "Play" (launch in real Slippi) state — shared by bundles and patches
  const [playingId, setPlayingId] = useState(null)
  const [playPercent, setPlayPercent] = useState(0)
  const [playMessage, setPlayMessage] = useState('')
  const [playError, setPlayError] = useState(null)
  const [playLaunched, setPlayLaunched] = useState(false)

  // Custom stages state (sub-page within stages mode)
  const [customStages, setCustomStages] = useState([])
  const [showCustomStages, setShowCustomStages] = useState(false)
  const [selectedCustomStage, setSelectedCustomStage] = useState(null)
  const [customStageImporting, setCustomStageImporting] = useState(false)

  // Custom characters state (sub-page within characters mode)
  const [customCharacters, setCustomCharacters] = useState([])
  const [showCustomCharacters, setShowCustomCharacters] = useState(false)
  const [selectedCustomCharacter, setSelectedCustomCharacter] = useState(null)
  const [customCharacterImporting, setCustomCharacterImporting] = useState(false)

  // Slippi retest dialog state (for retest from edit modal)
  const [retestingItem, setRetestingItem] = useState(null) // For retest dialog

  const [showSkinCreator, setShowSkinCreator] = useState(false) // Skin creator modal
  const [skinCreatorInitialCostume, setSkinCreatorInitialCostume] = useState(null) // For "edit from vault" flow

  const [showIsoScanModal, setShowIsoScanModal] = useState(false)

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

  // Fetch custom stages
  const fetchCustomStages = async () => {
    try {
      const response = await fetch(`${API_URL}/custom-stages/list`)
      const data = await response.json()
      if (data.success) {
        setCustomStages(data.stages || [])
      }
    } catch (err) {
      console.error('Failed to fetch custom stages:', err)
    }
  }

  // Custom stage import handler
  const handleCustomStageImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    setCustomStageImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${API_URL}/custom-stages/import-zip`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        await fetchCustomStages()
      } else {
        alert(data.error || 'Import failed')
      }
    } catch (err) {
      alert(`Import error: ${err.message}`)
    } finally {
      setCustomStageImporting(false)
    }
  }

  // Custom stage scan ISO handler
  const handleCustomStageScanIso = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    setCustomStageImporting(true)
    try {
      const response = await fetch(`${API_URL}/custom-stages/scan-iso`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isoPath: file.path })
      })
      const data = await response.json()
      if (data.success) {
        await fetchCustomStages()
        if (data.message) {
          alert(data.message)
        }
      } else {
        alert(data.error || 'Scan failed')
      }
    } catch (err) {
      alert(`Scan error: ${err.message}`)
    } finally {
      setCustomStageImporting(false)
    }
  }

  // Fetch custom characters
  const fetchCustomCharacters = async () => {
    try {
      const response = await fetch(`${API_URL}/custom-characters/list`)
      const data = await response.json()
      if (data.success) {
        setCustomCharacters(data.characters || [])
      }
    } catch (err) {
      console.error('Failed to fetch custom characters:', err)
    }
  }

  // Custom character import handler
  const handleCustomCharacterImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    setCustomCharacterImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${API_URL}/custom-characters/import-zip`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        await fetchCustomCharacters()
      } else {
        alert(data.error || 'Import failed')
      }
    } catch (err) {
      alert(`Import error: ${err.message}`)
    } finally {
      setCustomCharacterImporting(false)
    }
  }

  // Custom character scan ISO handler
  const handleCustomCharacterScanIso = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    setCustomCharacterImporting(true)
    try {
      const response = await fetch(`${API_URL}/custom-characters/scan-iso`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isoPath: file.path })
      })
      const data = await response.json()
      if (data.success) {
        await fetchCustomCharacters()
        if (data.message) {
          alert(data.message)
        }
      } else {
        alert(data.error || 'Scan failed')
      }
    } catch (err) {
      alert(`Scan error: ${err.message}`)
    } finally {
      setCustomCharacterImporting(false)
    }
  }

  // Drag and drop hook
  const {
    draggedItem,
    dragOverIndex,
    previewOrder,
    reordering,
    setReordering,
    justDraggedRef,
    isDraggingActive,
    justDroppedId,
    dragTargetFolder,
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

  // Folder expansion state — owned here so it persists when CharacterDetailView
  // unmounts on Back. The rest of folder management (useFolderManagement) now
  // lives inside CharacterDetailView, which this state is injected into.
  const [expandedFolders, setExpandedFolders] = useState({})

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
    showDuplicateDialog,
    duplicateDialogData,
    handleFileImport,
    handleSlippiChoice,
    handleDuplicateChoice
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
        // Dedupe by id just in case
        const seen = new Set()
        const uniqueBundles = data.bundles.filter(b => {
          if (seen.has(b.id)) return false
          seen.add(b.id)
          return true
        })
        setBundles(uniqueBundles)
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
    fetchBundles,
    // Play (launch in real Slippi)
    playingId,
    setPlayPercent,
    setPlayMessage,
    setPlayError,
    setPlayLaunched
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
    refreshManagedSkinState,
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
    },
    onUpdateEditingItemData: (updatedData) => {
      if (setEditingItemRef.current) {
        setEditingItemRef.current(prev => (
          prev?.type === 'costume' &&
          prev.data.id === updatedData.id &&
          prev.data.character === updatedData.character
            ? {
                ...prev,
                data: {
                  ...prev.data,
                  ...updatedData
                }
              }
            : prev
        ))
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
    replaceStageScreenshotWithCapture,
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

  const handleCostumeAssetsUpdated = useCallback(async ({ character, skinIds }) => {
    const targetIds = [...new Set((skinIds || []).filter(Boolean))]
    if (!character || targetIds.length === 0) return

    setLastImageUpdate(Date.now())

    if (onRefresh) {
      await onRefresh()
    }

    const shouldSyncEditingItem = editingItem?.type === 'costume' &&
      editingItem.data.character === character &&
      targetIds.includes(editingItem.data.id)

    const shouldSyncCspManager = cspManagerSkin?.character === character &&
      targetIds.includes(cspManagerSkin.id)

    if (!shouldSyncEditingItem && !shouldSyncCspManager) {
      return
    }

    const syncTargets = [
      shouldSyncEditingItem ? editingItem.data.id : null,
      shouldSyncCspManager ? cspManagerSkin.id : null
    ].filter((value, index, array) => value && array.indexOf(value) === index)

    for (const skinId of syncTargets) {
      await refreshManagedSkinState(character, skinId, { refreshParent: false })
    }
  }, [cspManagerSkin, editingItem, onRefresh, refreshManagedSkinState, setLastImageUpdate])

  // Fetch stage variants and custom stages when in stages mode
  useEffect(() => {
    if (mode === 'stages') {
      fetchStageVariants()
      fetchCustomStages()
    }
  }, [mode, metadata])

  // Fetch custom characters when in characters mode
  useEffect(() => {
    if (mode === 'characters') {
      fetchCustomCharacters()
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

  // "Play": build the ISO if missing, (bundles) load the texture pack, then launch
  // the user's real Slippi Dolphin. Progress arrives via play_* socket events.
  const startPlay = async (kind, id) => {
    const slippiPath = localStorage.getItem('slippi_dolphin_path')
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    if (!slippiPath) {
      alert('Slippi Dolphin path not set. Please configure it in Settings.')
      return
    }
    setPlayingId(id)
    setPlayPercent(0)
    setPlayMessage('Starting...')
    setPlayError(null)
    setPlayLaunched(false)
    try {
      const route = kind === 'bundle' ? `bundle/play/${id}` : `xdelta/play/${id}`
      const response = await fetch(`${API_URL}/${route}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slippiPath, vanillaIsoPath })
      })
      const data = await response.json()
      if (!data.success) setPlayError(data.error || 'Failed to start')
    } catch (err) {
      setPlayError(`Play error: ${err.message}`)
    }
  }
  const handlePlayBundle = (bundle) => startPlay('bundle', bundle.id)
  const handlePlayPatch = (patch) => startPlay('patch', patch.id)
  const dismissPlay = () => { setPlayingId(null); setPlayError(null); setPlayLaunched(false) }

  // Auto-dismiss the overlay shortly after a successful launch.
  useEffect(() => {
    if (!playLaunched) return
    const t = setTimeout(() => { setPlayingId(null); setPlayLaunched(false) }, 2500)
    return () => clearTimeout(t)
  }, [playLaunched])

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




  // If a custom character is selected, show its detail view
  if (selectedCustomCharacter) {
    return (
      <CustomCharacterDetailView
        character={selectedCustomCharacter}
        onBack={() => setSelectedCustomCharacter(null)}
        onDelete={() => { setSelectedCustomCharacter(null); fetchCustomCharacters(); }}
        onRename={(updated) => {
          setSelectedCustomCharacter(updated)
          fetchCustomCharacters()
        }}
        API_URL={API_URL}
      />
    )
  }

  // If custom characters sub-page is open, show the grid
  if (showCustomCharacters) {
    return (
      <div className="storage-viewer">
        <ModeToolbar
          mode={mode}
          onModeChange={(newMode) => {
            setMode(newMode)
            setShowCustomCharacters(false)
            setSelectedCustomCharacter(null)
            if (newMode === 'characters') {
              setSelectedStage(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'stages') {
              setSelectedCharacter(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'patches') {
              setSelectedCharacter(null)
              setSelectedStage(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'menus') {
              setSelectedCharacter(null)
              setSelectedStage(null)
            }
          }}
        />
        <CustomCharactersGrid
          customCharacters={customCharacters}
          isLoading={isLoading}
          onSelectCharacter={setSelectedCustomCharacter}
          onBack={() => setShowCustomCharacters(false)}
          onImportZip={handleCustomCharacterImport}
          onScanIso={handleCustomCharacterScanIso}
          importing={customCharacterImporting}
        />
      </div>
    )
  }

  // If a custom stage is selected, show its detail view
  if (selectedCustomStage) {
    return (
      <CustomStageDetailView
        stage={selectedCustomStage}
        onBack={() => setSelectedCustomStage(null)}
        onDelete={() => { setSelectedCustomStage(null); fetchCustomStages(); }}
        onRename={(updatedStage) => {
          setSelectedCustomStage(updatedStage)
          fetchCustomStages()
        }}
        API_URL={API_URL}
      />
    )
  }

  // If custom stages sub-page is open, show the grid
  if (showCustomStages) {
    return (
      <div className="storage-viewer">
        <ModeToolbar
          mode={mode}
          onModeChange={(newMode) => {
            setMode(newMode)
            setShowCustomStages(false)
            setSelectedCustomStage(null)
            if (newMode === 'characters') {
              setSelectedStage(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'stages') {
              setSelectedCharacter(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'patches') {
              setSelectedCharacter(null)
              setSelectedStage(null)
              setSelectedMenuType(null)
              setSelectedMenuModType(null)
            } else if (newMode === 'menus') {
              setSelectedCharacter(null)
              setSelectedStage(null)
            }
          }}
        />
        <CustomStagesGrid
          customStages={customStages}
          isLoading={isLoading}
          onSelectStage={setSelectedCustomStage}
          onBack={() => setShowCustomStages(false)}
          onImportZip={handleCustomStageImport}
          onScanIso={handleCustomStageScanIso}
          importing={customStageImporting}
          onRefresh={fetchCustomStages}
        />
      </div>
    )
  }

  // If a stage is selected, show its variants
  if (selectedStage) {
    return (
      <StageDetailView
        selectedStage={selectedStage}
        stageVariants={stageVariants}
        onBack={() => setSelectedStage(null)}
        onRefresh={onRefresh}
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
        replaceStageScreenshotWithCapture={replaceStageScreenshotWithCapture}
        // CSP Manager
        showCspManager={showCspManager}
        cspManagerSkin={cspManagerSkin}
        pendingMainCspPreview={pendingMainCspPreview}
        hdCspInfo={hdCspInfo}
        compareSliderPosition={compareSliderPosition}
        alternativeCsps={alternativeCsps}
        capturingHdCsp={capturingHdCsp}
        closeCspManager={closeCspManager}
        handleCspManagerMainChange={handleCspManagerMainChange}
        handleCompareSliderStart={handleCompareSliderStart}
        handleSwapCsp={handleSwapCsp}
        handleRemoveAlternativeCsp={handleRemoveAlternativeCsp}
        handleAddAlternativeCsp={handleAddAlternativeCsp}
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
        // Folder expansion state (persists here across character navigation)
        expandedFolders={expandedFolders}
        setExpandedFolders={setExpandedFolders}
        // Shared state clusters (same hook instances also feed StageDetailView
        // and the grid-level modals below)
        dragDrop={{
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
        }}
        editModal={{
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
          handleSave,
          handleDelete,
          handleExport,
          handleCancel,
          confirmDelete,
          cancelDelete
        }}
        cspManager={{
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
        }}
        slippiDialog={{
          showSlippiDialog,
          slippiDialogData,
          retestingItem,
          handleRetestFixChoice,
          handleSlippiChoice,
          handleSlippiRetest,
          handleSlippiOverride
        }}
        contextMenuApi={{
          contextMenu,
          handleSkinContextMenu,
          handleMoveToTop,
          handleMoveToBottom
        }}
        skinCreator={{
          showSkinCreator,
          openSkinCreator,
          closeSkinCreator,
          startSkinCreatorFromVault,
          skinCreatorInitialCostume
        }}
        // Identity / data / callbacks
        onSkinCreatorChange={onSkinCreatorChange}
        onRefresh={onRefresh}
        onCostumesUpdated={handleCostumeAssetsUpdated}
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
          setShowCustomStages(false)
          setSelectedCustomStage(null)
          setShowCustomCharacters(false)
          setSelectedCustomCharacter(null)
          if (newMode === 'characters') {
            setSelectedStage(null)
            setSelectedMenuType(null)
            setSelectedMenuModType(null)
          } else if (newMode === 'stages') {
            setSelectedCharacter(null)
            setSelectedMenuType(null)
            setSelectedMenuModType(null)
          } else if (newMode === 'patches') {
            setSelectedCharacter(null)
            setSelectedStage(null)
            setSelectedMenuType(null)
            setSelectedMenuModType(null)
          } else if (newMode === 'menus') {
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
        onShowIsoScanModal={() => setShowIsoScanModal(true)}
      />

      {showIsoScanModal && (
        <IsoScanModal
          onClose={() => setShowIsoScanModal(false)}
          onRefresh={onRefresh}
        />
      )}

      {mode === 'characters' ? (
        <CharactersGrid
          characters={characters}
          allCharacters={allCharacters}
          isLoading={isLoading}
          onSelectCharacter={setSelectedCharacter}
          customCharacterCount={customCharacters.length}
          onOpenCustomCharacters={() => setShowCustomCharacters(true)}
        />
      ) : mode === 'stages' ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.75rem' }}>
            <button
              className="mode-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setShowBulkCapture(true) }}
              title="Capture clean in-game screenshots for many DAS variants at once"
            >
              📸 Bulk Capture Screenshots
            </button>
          </div>
          <StagesGrid
            stageVariants={stageVariants}
            isLoading={isLoading}
            onSelectStage={setSelectedStage}
            customStageCount={customStages.length}
            onOpenCustomStages={() => setShowCustomStages(true)}
          />
        </>
      ) : mode === 'patches' ? (
        <PatchesGrid
          xdeltaPatches={xdeltaPatches}
          bundles={bundles}
          onEditPatch={handleEditXdelta}
          onBuildIso={handleBuildXdeltaIso}
          onShowCreateModal={() => setShowXdeltaCreateModal(true)}
          onEditBundle={handleEditBundle}
          onInstallBundle={handleInstallBundle}
          onPlayBundle={handlePlayBundle}
          onPlayPatch={handlePlayPatch}
          playingId={playingId}
          playPercent={playPercent}
        />
      ) : selectedMenuType ? (
        <div className="grid-wrapper">
          {!menuDetailOpen && (
            <div className="vault-breadcrumb">
              <button
                className="mode-btn"
                onMouseEnter={playHoverSound}
                onClick={() => {
                  playSound('boop')
                  if (selectedMenuModType) {
                    setSelectedMenuModType(null)
                  } else {
                    setSelectedMenuType(null)
                  }
                }}
              >
                ← Back
              </button>
              <span className="vault-breadcrumb-path">
                Menus / {selectedMenuType.toUpperCase()}
                {selectedMenuModType ? ` / ${selectedMenuModType.replace('_', ' ')}` : ''}
              </span>
            </div>
          )}

          {selectedMenuType === 'css' && !selectedMenuModType && (
            <CssMenuTypesGrid onSelectModType={setSelectedMenuModType} />
          )}

          {selectedMenuType === 'css' && selectedMenuModType === 'icon_grid' && (
            <IconGridModsView onDetailChange={setMenuDetailOpen} />
          )}

          {selectedMenuType === 'css' && selectedMenuModType === 'background' && (
            <BackgroundModsView />
          )}

          {selectedMenuType === 'css' && selectedMenuModType === 'doors' && (
            <DoorModsView />
          )}

          {selectedMenuType === 'sss' && !selectedMenuModType && (
            <SssMenuTypesGrid onSelectModType={setSelectedMenuModType} />
          )}

          {selectedMenuType === 'sss' && selectedMenuModType === 'background' && (
            <BackgroundModsView />
          )}

          {selectedMenuType === 'pause' && (
            <PauseModsView onDetailChange={setMenuDetailOpen} />
          )}
        </div>
      ) : (
        <div className="grid-wrapper">
          <MenusGrid onSelectMenuType={setSelectedMenuType} />
        </div>
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
        onDownload={handleDownloadPatch}
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
        onDownload={handleDownloadBundle}
        BACKEND_URL={BACKEND_URL}
      />

      {/* XDelta Create Patch Modal */}
      <XdeltaCreateModal
        show={showXdeltaCreateModal}
        xdeltaCreateState={xdeltaCreateState}
        xdeltaCreateData={xdeltaCreateData}
        setXdeltaCreateData={setXdeltaCreateData}
        xdeltaCreateProgress={xdeltaCreateProgress}
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

      <DuplicateImportDialog
        show={showDuplicateDialog}
        data={duplicateDialogData}
        onChoice={handleDuplicateChoice}
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

      {playingId && (
        <div className="play-overlay" onClick={(playError || playLaunched) ? dismissPlay : undefined}>
          <div className="play-card" onClick={(e) => e.stopPropagation()}>
            {playError ? (
              <>
                <div className="play-icon error">✕</div>
                <p className="play-card-msg">{playError}</p>
                <button className="btn-secondary" onClick={dismissPlay}>Close</button>
              </>
            ) : playLaunched ? (
              <>
                <p className="play-card-msg">Launched — switch to Dolphin!</p>
              </>
            ) : (
              <>
                <div className="play-spinner" />
                <p className="play-card-msg">{playMessage}</p>
                <div className="play-bar"><div className="play-bar-fill" style={{ width: `${playPercent}%` }} /></div>
                <p className="play-card-pct">{playPercent}%</p>
              </>
            )}
          </div>
        </div>
      )}

      <BulkStageCaptureModal
        show={showBulkCapture}
        onClose={() => setShowBulkCapture(false)}
        onSaved={() => { fetchStageVariants(); setLastImageUpdate(Date.now()) }}
      />
    </div>
  )
}

