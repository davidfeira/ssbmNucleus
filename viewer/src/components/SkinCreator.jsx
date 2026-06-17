import { useState, useEffect, useRef } from 'react'
import { usePanelResize } from '../hooks/usePanelResize'
import { playSound } from '../utils/sounds'
import { appConfirm } from '../utils/appDialogs'
import { API_URL } from '../config'
import { useCanvasScale } from './skincreator/useCanvasScale'
import { useUndoRedo } from './skincreator/useUndoRedo'
import { usePaintCanvas } from './skincreator/usePaintCanvas'
import { useColorPalette } from './skincreator/useColorPalette'
import { useViewerCamera } from './skincreator/useViewerCamera'
import { useViewerPosition } from './skincreator/useViewerPosition'
import { requestExportDat, base64ToBlob } from './skincreator/datUtils'
import SkinCreatorHeader from './skincreator/SkinCreatorHeader'
import CostumeSelectStep from './skincreator/CostumeSelectStep'
import PaintToolbar from './skincreator/PaintToolbar'
import CanvasFloatingActions from './skincreator/CanvasFloatingActions'
import ColorPalettePanel from './skincreator/ColorPalettePanel'
import TextureStrip from './skincreator/TextureStrip'
import SaveModal from './skincreator/SaveModal'
import './SkinCreator.css'

export default function SkinCreator({
  isOpen,
  onClose,
  selectedCharacter,
  onSkinCreatorChange,
  onRefresh,
  initialCostume,
  // AI Skin Studio option on the base-costume step (gated by /ai-status)
  aiStudioEnabled,
  aiReady,
  onOpenAiStudio,
  // AI Model Studio option (gated by /model-lab/status)
  modelStudioEnabled,
  onOpenModelStudio
}) {
  // State
  const [skinCreatorStep, setSkinCreatorStep] = useState('select') // 'select' or 'edit'
  const [vanillaCostumes, setVanillaCostumes] = useState([])
  const [selectedVanillaCostume, setSelectedVanillaCostume] = useState(null)
  const [skinCreatorLoading, setSkinCreatorLoading] = useState(false)
  const [skinCreatorError, setSkinCreatorError] = useState(null)
  const [viewerWs, setViewerWs] = useState(null)
  const [modelTextures, setModelTextures] = useState([])
  const [selectedTextureIndex, setSelectedTextureIndex] = useState(null)
  const skinCreatorCanvasRef = useRef(null)
  const paintCanvasRef = useRef(null)

  const [editedTextures, setEditedTextures] = useState({}) // { [index]: dataUrl }
  const editedTexturesRef = useRef({}) // Ref for interval callback access
  const [isDirty, setIsDirty] = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [skinName, setSkinName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [skinCreatorReconnecting, setSkinCreatorReconnecting] = useState(false)
  const [skinCreatorReconnectAttempts, setSkinCreatorReconnectAttempts] = useState(0)
  const skinCreatorReconnectTimeoutRef = useRef(null)
  const skinCreatorMaxReconnectAttempts = 3
  const [poseOptions, setPoseOptions] = useState([])
  const [selectedPoseName, setSelectedPoseName] = useState('')
  const [defaultPoseName, setDefaultPoseName] = useState('')
  const activeStartPoseRef = useRef(null)

  // Connection health and auto-refresh
  const autoRefreshIntervalRef = useRef(null)
  const pingIntervalRef = useRef(null)
  const lastMessageTimeRef = useRef(Date.now()) // Track last message received (any type)
  const [connectionFailed, setConnectionFailed] = useState(false)

  const exportDatResolverRef = useRef(null) // For promise-based exportDat with Electron IPC
  // The SOURCE costume's dat filename (e.g. PlFxNr.dat), captured from the
  // viewer-paths response. Saves must keep a Pl* dat name -- the import
  // pipeline only recognizes Pl*-stemmed DATs as costumes.
  const sourceDatNameRef = useRef(null)

  // Panel resize hook
  const {
    sizes: panelSizes,
    handleRightPanelResize,
    handleTextureStripResize,
    handlePreviewResize,
  } = usePanelResize()

  // Check if Electron API is available
  const hasElectron = typeof window !== 'undefined' && window.electron?.viewerStart

  const customCharacterSlugFromKey = (key) => {
    const match = typeof key === 'string'
      ? key.match(/^custom_characters\/([^/]+)\/(?:skins|costumes)$/)
      : null
    return match?.[1] || null
  }

  const getPoseCharacterKey = (key) => {
    const slug = customCharacterSlugFromKey(key)
    return slug ? `custom_characters/${slug}/costumes` : key
  }

  const resolveViewerPose = async (characterKey, requestedPoseName) => {
    const slug = customCharacterSlugFromKey(characterKey)
    if (!slug) {
      activeStartPoseRef.current = null
      setPoseOptions([])
      setSelectedPoseName('')
      setDefaultPoseName('')
      return null
    }

    const poseCharacter = getPoseCharacterKey(characterKey)
    let defaultPose = ''
    let poses = []

    try {
      const [detailRes, posesRes] = await Promise.all([
        fetch(`${API_URL}/custom-characters/${slug}/detail`),
        fetch(`${API_URL}/storage/poses/list/${encodeURIComponent(poseCharacter)}`)
      ])
      const detailData = await detailRes.json()
      const posesData = await posesRes.json()
      defaultPose = detailData.success ? (detailData.detail?.default_pose || '') : ''
      poses = posesData.success ? (posesData.poses || []) : []
    } catch (err) {
      console.error('[SkinCreator] Failed to load custom character poses:', err)
    }

    setDefaultPoseName(defaultPose)
    setPoseOptions(poses)

    const hasPose = (name) => Boolean(name) && poses.some(pose => pose.name === name)
    const poseName = requestedPoseName !== undefined
      ? requestedPoseName
      : (hasPose(selectedPoseName) ? selectedPoseName : defaultPose)
    setSelectedPoseName(poseName || '')

    if (!poseName) {
      activeStartPoseRef.current = null
      return null
    }

    try {
      const sceneRes = await fetch(
        `${API_URL}/storage/poses/scene-file/${encodeURIComponent(poseCharacter)}/${encodeURIComponent(poseName)}`
      )
      const sceneData = await sceneRes.json()
      if (!sceneData.success) {
        throw new Error(sceneData.error || 'Failed to load pose scene')
      }
      const pose = {
        name: poseName,
        sceneFile: sceneData.sceneFile,
        animSymbol: sceneData.animSymbol,
        frame: sceneData.frame || 0
      }
      activeStartPoseRef.current = pose
      return pose
    } catch (err) {
      console.error('[SkinCreator] Failed to apply pose:', err)
      activeStartPoseRef.current = null
      return null
    }
  }

  // Canvas container sizing for dynamic scaling
  const { canvasContainerRef, updateCanvasScale } = useCanvasScale({
    skinCreatorStep,
    selectedTextureIndex,
    modelTextures,
    paintCanvasRef
  })

  const sendTextureUpdate = () => {
    const canvas = paintCanvasRef.current
    if (!canvas || !hasElectron || !viewerWs) return
    if (selectedTextureIndex === null) return

    const ctx = canvas.getContext('2d')
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)

    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = canvas.width
    tempCanvas.height = canvas.height
    const tempCtx = tempCanvas.getContext('2d')
    tempCtx.putImageData(imageData, 0, 0)

    const dataUrl = tempCanvas.toDataURL('image/png')
    const base64 = dataUrl.replace('data:image/png;base64,', '')

    try {
      if (hasElectron) {
        window.electron.viewerSend({
          type: 'updateTexture',
          index: selectedTextureIndex,
          data: base64
        })
      }

      setEditedTextures(prev => ({ ...prev, [selectedTextureIndex]: dataUrl }))
      setIsDirty(true)
    } catch (err) {
      console.error('Error sending updateTexture:', err)
    }
  }

  // Undo/Redo stack
  const { undoStack, redoStack, saveToUndoStack, undo, redo } = useUndoRedo({
    paintCanvasRef,
    sendTextureUpdate,
    selectedTextureIndex,
    isOpen,
    skinCreatorStep
  })

  // Drawing tools state and paint canvas handlers
  const {
    activeTool,
    setActiveTool,
    drawColor,
    setDrawColor,
    brushSize,
    setBrushSize,
    isDrawingRef,
    handlePaintMouseDown,
    handlePaintMouseMove,
    handlePaintMouseUp
  } = usePaintCanvas({ paintCanvasRef, saveToUndoStack, sendTextureUpdate })

  // Color Palette
  const palette = useColorPalette({
    modelTextures,
    editedTextures,
    setEditedTextures,
    setIsDirty,
    hasElectron,
    viewerWs
  })

  // 3D viewer camera controls
  const {
    handleViewerMouseDown,
    handleViewerMouseMove,
    handleViewerMouseUp,
    handleViewerWheel,
    handleViewerContextMenu
  } = useViewerCamera({ hasElectron, viewerWs })

  // Keep embedded viewer window positioned over the 3D preview container
  const updateViewerPosition = useViewerPosition({
    skinCreatorCanvasRef,
    hasElectron,
    viewerWs,
    skinCreatorStep,
    panelSizes
  })

  // Keep editedTexturesRef in sync with state for interval callback access
  useEffect(() => {
    editedTexturesRef.current = editedTextures
  }, [editedTextures])

  // Notify parent when skin creator opens/closes
  useEffect(() => {
    onSkinCreatorChange?.(isOpen)
  }, [isOpen, onSkinCreatorChange])

  // Load costumes when opening
  useEffect(() => {
    if (isOpen && selectedCharacter && skinCreatorStep === 'select' && !initialCostume) {
      loadVanillaCostumes(selectedCharacter)
    }
  }, [isOpen, selectedCharacter, skinCreatorStep, initialCostume])

  // Handle initialCostume for "edit from vault" flow
  useEffect(() => {
    if (isOpen && initialCostume) {
      startSkinCreatorFromVault(initialCostume)
    }
  }, [isOpen, initialCostume])

  // Load vanilla costumes
  const loadVanillaCostumes = async (character) => {
    try {
      setSkinCreatorLoading(true)
      setSkinCreatorError(null)
      const response = await fetch(`${API_URL}/vanilla/costumes/${character}`)
      const data = await response.json()
      if (data.success) {
        setVanillaCostumes(data.costumes)
      } else {
        setSkinCreatorError(data.error)
      }
    } catch (err) {
      setSkinCreatorError(err.message)
    } finally {
      setSkinCreatorLoading(false)
    }
  }

  // Handle viewer messages (Electron IPC)
  const handleViewerMessage = (msg) => {
    console.log('[SkinCreator] Received viewer message:', msg.type, msg)
    lastMessageTimeRef.current = Date.now()

    if (msg.type === 'textureList') {
      if (modelTextures.length === 0 && msg.textures?.length > 0) {
        setSelectedTextureIndex(0)
      }
      setModelTextures(msg.textures || [])
    } else if (msg.type === 'fullTexture') {
      console.log('Received fullTexture', { index: msg.index, width: msg.width, height: msg.height })
      if (msg.error) return
      if (!msg.data) return
      const canvas = paintCanvasRef.current
      if (canvas) {
        const img = new Image()
        img.onload = () => {
          canvas.width = msg.width
          canvas.height = msg.height
          const ctx = canvas.getContext('2d')
          ctx.imageSmoothingEnabled = false
          ctx.drawImage(img, 0, 0)
          updateCanvasScale(canvas, msg.width, msg.height)
        }
        img.src = `data:image/png;base64,${msg.data}`
      }
    } else if (msg.type === 'ready') {
      setSkinCreatorLoading(false)
      setSkinCreatorStep('edit')
      setConnectionFailed(false)
      // Position the viewer window after a brief delay to ensure DOM is ready
      setTimeout(() => updateViewerPosition(), 100)
      // Set viewer to animation mode (not CSP mode) - fill the viewport freely
      window.electron.viewerSetCspMode(false)
      window.electron.viewerSetGrid(true)
      window.electron.viewerSetBackground(true)
      // Request textures
      window.electron.viewerSend({ type: 'getTextures' })
      if (activeStartPoseRef.current?.animSymbol) {
        window.electron.viewerLoadAnim(activeStartPoseRef.current.animSymbol)
      }
    } else if (msg.type === 'exportDat') {
      // Handle exportDat response for save/download operations
      if (exportDatResolverRef.current) {
        if (msg.success) {
          exportDatResolverRef.current.resolve(msg.data)
        } else {
          exportDatResolverRef.current.reject(new Error(msg.error || 'Export failed'))
        }
        exportDatResolverRef.current = null
      }
    } else if (msg.type === 'animLoaded') {
      const pose = activeStartPoseRef.current
      if (pose?.animSymbol && msg.symbol === pose.animSymbol) {
        window.electron.viewerAnimSetFrame(pose.frame || 0)
        window.electron.viewerAnimPause()
      }
    }
  }

  // Start viewer with selected costume (Electron IPC)
  const startSkinCreatorViewer = async (costume, poseNameOverride) => {
    try {
      setSkinCreatorLoading(true)
      setSkinCreatorError(null)
      setSelectedVanillaCostume(costume)

      if (!hasElectron) {
        throw new Error('Electron environment required for embedded viewer')
      }

      // Get file paths from Flask (no viewer spawning)
      const response = await fetch(`${API_URL}/viewer/paths-vanilla`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
          costumeCode: costume.code
        })
      })

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error)
      }
      sourceDatNameRef.current = (data.datFile || '').split(/[\\/]/).pop() || null
      const pose = await resolveViewerPose(selectedCharacter, poseNameOverride)

      // Set up message listener
      const cleanup = window.electron.onViewerMessage(handleViewerMessage)
      setViewerWs({ cleanup }) // Store cleanup function

      // Start embedded viewer via Electron IPC
      await window.electron.viewerStart({
        datFile: data.datFile,
        sceneFile: pose?.sceneFile || data.sceneFile,
        ajFile: data.ajFile,
        dataFile: data.dataFile,
        logsPath: data.logsPath
      })

      // Start auto-refresh interval (every 5 seconds, pauses while drawing)
      lastMessageTimeRef.current = Date.now()
      autoRefreshIntervalRef.current = setInterval(() => {
        if (isDrawingRef.current) return
        // Resend any edited textures to ensure 3D viewer stays in sync
        Object.entries(editedTexturesRef.current).forEach(([idx, dataUrl]) => {
          const base64 = dataUrl.replace('data:image/png;base64,', '')
          window.electron.viewerSend({
            type: 'updateTexture',
            index: parseInt(idx),
            data: base64
          })
        })
      }, 5000)

    } catch (err) {
      setSkinCreatorError(err.message)
      setSkinCreatorLoading(false)
    }
  }

  // Start from vault costume (for editing existing costumes) - Electron IPC
  const startSkinCreatorFromVault = async (costume, poseNameOverride) => {
    console.log('[SkinCreator] startSkinCreatorFromVault called with:', costume)
    try {
      const character = costume.character || selectedCharacter
      if (!character) {
        throw new Error('No character specified')
      }

      if (!hasElectron) {
        throw new Error('Electron environment required for embedded viewer')
      }

      setSkinCreatorLoading(true)
      setSkinCreatorError(null)
      setSelectedVanillaCostume({ code: costume.id, colorName: costume.color })

      // Get file paths from Flask (no viewer spawning)
      const response = await fetch(`${API_URL}/viewer/paths-vault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: character,
          costumeId: costume.id
        })
      })

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error)
      }
      sourceDatNameRef.current = (data.datFile || '').split(/[\\/]/).pop() || null
      const pose = await resolveViewerPose(character, poseNameOverride)

      // Set up message listener
      console.log('[SkinCreator] Setting up message listener for vault...')
      const cleanup = window.electron.onViewerMessage(handleViewerMessage)
      setViewerWs({ cleanup }) // Store cleanup function

      // Start embedded viewer via Electron IPC
      console.log('[SkinCreator] Calling viewerStart with paths:', data)
      const result = await window.electron.viewerStart({
        datFile: data.datFile,
        sceneFile: pose?.sceneFile || data.sceneFile,
        ajFile: data.ajFile,
        dataFile: data.dataFile,
        logsPath: data.logsPath
      })
      console.log('[SkinCreator] viewerStart returned:', result)

      // Start auto-refresh interval (every 5 seconds, pauses while drawing)
      lastMessageTimeRef.current = Date.now()
      autoRefreshIntervalRef.current = setInterval(() => {
        if (isDrawingRef.current) return
        // Resend any edited textures to ensure 3D viewer stays in sync
        Object.entries(editedTexturesRef.current).forEach(([idx, dataUrl]) => {
          const base64 = dataUrl.replace('data:image/png;base64,', '')
          window.electron.viewerSend({
            type: 'updateTexture',
            index: parseInt(idx),
            data: base64
          })
        })
      }, 5000)

    } catch (err) {
      console.error('[SkinCreator] Error in startSkinCreatorFromVault:', err)
      setSkinCreatorError(err.message)
      setSkinCreatorLoading(false)
    }
  }

  // Close and cleanup
  const closeSkinCreator = async (force = false) => {
    if (isDirty && !force) {
      const confirmed = await appConfirm('You have unsaved changes. Are you sure you want to close?', {
        title: 'Discard Changes',
        confirmText: 'Close',
      })
      if (!confirmed) return
    }
    playSound('back')

    if (skinCreatorReconnectTimeoutRef.current) {
      clearTimeout(skinCreatorReconnectTimeoutRef.current)
      skinCreatorReconnectTimeoutRef.current = null
    }

    // Clear ping and auto-refresh intervals
    clearAllIntervals()

    setSkinCreatorError('closing')

    // Clean up Electron IPC listener
    if (viewerWs?.cleanup) {
      viewerWs.cleanup()
    }
    setViewerWs(null)

    // Stop embedded viewer via Electron IPC
    if (hasElectron) {
      try {
        await window.electron.viewerStop()
      } catch (e) {
        // Ignore errors on cleanup
      }
    }

    // Reset state
    sourceDatNameRef.current = null
    setSkinCreatorStep('select')
    setVanillaCostumes([])
    setSelectedVanillaCostume(null)
    setSkinCreatorError(null)
    setModelTextures([])
    setSelectedTextureIndex(null)
    setEditedTextures({})
    setIsDirty(false)
    setSkinCreatorReconnecting(false)
    setSkinCreatorReconnectAttempts(0)
    setConnectionFailed(false)

    // Reset color palette
    palette.clearPaletteState()

    onClose?.()
  }

  // Refresh textures - resend all edited textures to viewer (Electron IPC)
  const refreshTextures = () => {
    if (hasElectron && viewerWs) {
      // Resend any edited textures to ensure 3D viewer is in sync
      Object.entries(editedTextures).forEach(([idx, dataUrl]) => {
        const base64 = dataUrl.replace('data:image/png;base64,', '')
        window.electron.viewerSend({
          type: 'updateTexture',
          index: parseInt(idx),
          data: base64
        })
      })
    }
  }

  // Handle reconnect after connection failure
  const handleReconnect = () => {
    setConnectionFailed(false)
    setSkinCreatorError(null)
    if (initialCostume) {
      startSkinCreatorFromVault(initialCostume)
    } else if (selectedVanillaCostume) {
      startSkinCreatorViewer(selectedVanillaCostume)
    }
  }

  // Clear all intervals helper
  const clearAllIntervals = () => {
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current)
      autoRefreshIntervalRef.current = null
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }

  const cleanupViewerConnection = async () => {
    clearAllIntervals()
    if (viewerWs?.cleanup) {
      viewerWs.cleanup()
    }
    setViewerWs(null)
    if (hasElectron) {
      try {
        await window.electron.viewerStop()
      } catch (e) {
        // Ignore viewer restart cleanup errors
      }
    }
  }

  const handlePoseChange = async (poseName) => {
    setSelectedPoseName(poseName)
    await cleanupViewerConnection()
    setSkinCreatorLoading(true)
    setConnectionFailed(false)
    if (initialCostume) {
      await startSkinCreatorFromVault(initialCostume, poseName)
    } else if (selectedVanillaCostume) {
      await startSkinCreatorViewer(selectedVanillaCostume, poseName)
    }
  }

  // Load texture onto paint canvas when selected
  useEffect(() => {
    if (selectedTextureIndex === null || !modelTextures[selectedTextureIndex]) return

    const tex = modelTextures[selectedTextureIndex]
    const canvas = paintCanvasRef.current
    if (!canvas) return

    const editedData = editedTextures[selectedTextureIndex]
    const imgSrc = editedData || (tex.thumbnail ? `data:image/png;base64,${tex.thumbnail}` : null)

    if (!imgSrc) return

    const img = new Image()
    img.onload = () => {
      canvas.width = tex.width
      canvas.height = tex.height
      const ctx = canvas.getContext('2d')
      ctx.imageSmoothingEnabled = false
      ctx.drawImage(img, 0, 0, tex.width, tex.height)
      updateCanvasScale(canvas, tex.width, tex.height)
    }
    img.src = imgSrc
  }, [selectedTextureIndex, modelTextures, editedTextures, updateCanvasScale])

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty])

  // Export texture as PNG
  const exportTexture = () => {
    if (selectedTextureIndex === null || !modelTextures[selectedTextureIndex]) return
    const canvas = paintCanvasRef.current
    if (!canvas) return

    const tex = modelTextures[selectedTextureIndex]
    const dataUrl = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `${tex.name || `texture_${selectedTextureIndex}`}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  // Import texture from PNG
  const importTexture = (e) => {
    const file = e.target.files?.[0]
    if (!file || selectedTextureIndex === null) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const img = new Image()
      img.onload = () => {
        const canvas = paintCanvasRef.current
        if (!canvas) return

        // Save to undo stack before importing
        saveToUndoStack()

        const ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.imageSmoothingEnabled = false
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        sendTextureUpdate()
      }
      img.src = event.target.result
    }
    reader.readAsDataURL(file)

    // Reset the input so the same file can be selected again
    e.target.value = ''
  }

  // Open save modal
  const openSaveModal = () => {
    const defaultName = `${selectedCharacter} Custom`
    setSkinName(defaultName)
    setSaveError(null)
    setShowSaveModal(true)
  }

  // Save to vault
  const handleSaveToVault = async () => {
    if (!skinName.trim()) {
      setSaveError('Please enter a name')
      return
    }

    if (!hasElectron) {
      setSaveError('Electron environment required')
      return
    }

    setIsSaving(true)
    setSaveError(null)

    try {
      // Use Electron IPC for export
      const base64Data = await requestExportDat(exportDatResolverRef)

      const datBlob = base64ToBlob(base64Data)

      // A skin from a custom character's library (pseudo key
      // custom_characters/<slug>/skins|costumes) saves back to that character's
      // Custom Skins — the generic intake would misfile its DAT under the donor
      // character. Keep the original Pl* DAT name: install keys costumes by it.
      const charKey = initialCostume?.character
      const customMatch = typeof charKey === 'string'
        ? charKey.match(/^custom_characters\/([^/]+)\//)
        : null

      const { default: JSZip } = await import('jszip')
      const zip = new JSZip()
      // Keep the SOURCE costume's Pl* dat name (the intake only recognizes
      // Pl*-stemmed DATs; custom-character installs key costumes by it).
      // The skin title still becomes the display name via custom_title/name.
      let datName = initialCostume?.dat_name
        || sourceDatNameRef.current
        || (selectedVanillaCostume?.code ? `${selectedVanillaCostume.code}.dat` : '')
      if (!/^pl/i.test(datName)) {
        datName = `${skinName.trim()}.dat`
      }
      zip.file(datName, datBlob)
      const zipBlob = await zip.generateAsync({ type: 'blob' })

      const formData = new FormData()
      formData.append('file', new File([zipBlob], `${skinName.trim()}.zip`))
      let saveUrl = `${API_URL}/import/file`
      if (customMatch) {
        formData.append('name', skinName.trim())
        if (selectedPoseName) {
          formData.append('poseName', selectedPoseName)
        }
        saveUrl = `${API_URL}/custom-characters/${customMatch[1]}/skins/add`
      } else {
        formData.append('custom_title', skinName.trim())
      }

      const response = await fetch(saveUrl, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Import failed')
      }

      const result = await response.json()

      setShowSaveModal(false)
      setIsDirty(false)
      setSkinName('')

      onRefresh?.()

      playSound(result.camera_sound ? 'camera' : 'newSkin')
      alert(`Skin "${skinName}" saved to vault!`)
    } catch (error) {
      console.error('Save error:', error)
      playSound('error')
      setSaveError(error.message)
    } finally {
      setIsSaving(false)
    }
  }

  // Download DAT file
  const handleDownloadDat = async () => {
    if (!hasElectron || !viewerWs) {
      alert('Not connected to viewer')
      return
    }

    try {
      // Use Electron IPC for export
      const base64Data = await requestExportDat(exportDatResolverRef)

      const datBlob = base64ToBlob(base64Data)

      const url = URL.createObjectURL(datBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedCharacter}_${selectedVanillaCostume?.colorName || 'custom'}.dat`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download: ' + error.message)
    }
  }

  if (!isOpen) return null

  return (
    <>
      <div className="skin-creator-overlay">
        <div className="skin-creator-modal">
          {/* Header - only shown in edit step */}
          {skinCreatorStep === 'edit' && (
            <SkinCreatorHeader
              selectedCharacter={selectedCharacter}
              selectedVanillaCostume={selectedVanillaCostume}
              isDirty={isDirty}
              poseOptions={poseOptions}
              selectedPoseName={selectedPoseName}
              defaultPoseName={defaultPoseName}
              onPoseChange={handlePoseChange}
              onSave={openSaveModal}
              onDownload={handleDownloadDat}
              onClose={() => closeSkinCreator()}
            />
          )}

          {/* Costume Selection Step */}
          {skinCreatorStep === 'select' && (
            <CostumeSelectStep
              initialCostume={initialCostume}
              onBack={() => closeSkinCreator()}
              vanillaCostumes={vanillaCostumes}
              selectedCharacter={selectedCharacter}
              loading={skinCreatorLoading}
              error={skinCreatorError}
              reconnecting={skinCreatorReconnecting}
              reconnectAttempts={skinCreatorReconnectAttempts}
              maxReconnectAttempts={skinCreatorMaxReconnectAttempts}
              onSelectCostume={startSkinCreatorViewer}
              aiStudioEnabled={aiStudioEnabled}
              aiReady={aiReady}
              onOpenAiStudio={onOpenAiStudio}
              modelStudioEnabled={modelStudioEnabled}
              onOpenModelStudio={onOpenModelStudio}
            />
          )}

          {/* Editor Step */}
          {skinCreatorStep === 'edit' && (
            <div className="skin-creator-body">
              {/* Main area: Canvas + Right Panel */}
              <div className="skin-creator-main">
                {/* Center - Paint Canvas */}
                <div className="skin-creator-canvas-area">
                  <PaintToolbar
                    undo={undo}
                    redo={redo}
                    canUndo={undoStack.length > 0}
                    canRedo={redoStack.length > 0}
                    drawColor={drawColor}
                    setDrawColor={setDrawColor}
                    activeTool={activeTool}
                    setActiveTool={setActiveTool}
                    brushSize={brushSize}
                    setBrushSize={setBrushSize}
                  />
                  <div
                    ref={canvasContainerRef}
                    className={`skin-creator-canvas tool-${activeTool}`}
                    onMouseDown={handlePaintMouseDown}
                    onMouseMove={handlePaintMouseMove}
                    onMouseUp={handlePaintMouseUp}
                    onMouseLeave={handlePaintMouseUp}
                  >
                    {selectedTextureIndex === null ? (
                      <div className="canvas-placeholder">
                        <span>Paint Canvas</span>
                        <p>Select a texture to start editing</p>
                      </div>
                    ) : (
                      <>
                        <canvas ref={paintCanvasRef} className="paint-canvas" draggable="false" />
                        {/* Floating Import/Export buttons */}
                        <CanvasFloatingActions
                          onImport={importTexture}
                          onExport={exportTexture}
                        />
                      </>
                    )}
                </div>
              </div>

                {/* Vertical resize handle between canvas and right panel */}
                <div
                  className="resize-handle vertical"
                  onMouseDown={handleRightPanelResize}
                />

                {/* Right Panel - 3D Preview + Tool Palette */}
                <div className="skin-creator-right-panel" style={{ width: panelSizes.rightPanelWidth }}>
                  {/* 3D Preview */}
                  <div className="skin-creator-3d-container" style={{ height: `calc(${panelSizes.previewHeightRatio * 100}% - 4px)` }}>
                    <div className="skin-creator-panel-header">
                      <span>3D Preview</span>
                      <button
                        className="refresh-btn"
                        onClick={refreshTextures}
                        title="Refresh textures"
                        disabled={!viewerWs || connectionFailed}
                      >
                        ↻
                      </button>
                    </div>
                    <div
                      ref={skinCreatorCanvasRef}
                      className="skin-creator-3d"
                      onMouseDown={handleViewerMouseDown}
                      onMouseMove={handleViewerMouseMove}
                      onMouseUp={handleViewerMouseUp}
                      onMouseLeave={handleViewerMouseUp}
                      onWheel={handleViewerWheel}
                      onContextMenu={handleViewerContextMenu}
                    >
                      {connectionFailed ? (
                        <div className="viewer-placeholder connection-failed">
                          <span>Connection Lost</span>
                          <button className="reconnect-btn" onClick={handleReconnect}>
                            Reconnect
                          </button>
                        </div>
                      ) : skinCreatorLoading ? (
                        <div className="viewer-placeholder">
                          <span>Loading...</span>
                        </div>
                      ) : skinCreatorReconnecting ? (
                        <div className="viewer-placeholder reconnecting">
                          <span>Reconnecting...</span>
                          <p>Attempt {skinCreatorReconnectAttempts}/{skinCreatorMaxReconnectAttempts}</p>
                        </div>
                      ) : (
                        <div className="viewer-hint">
                          Drag to rotate | Scroll to zoom | Right-drag to pan
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Horizontal resize handle between 3D preview and tool palette */}
                  <div
                    className="resize-handle horizontal"
                    onMouseDown={handlePreviewResize}
                  />

                  {/* Tool Palette */}
                  <ColorPalettePanel
                    height={`calc(${(1 - panelSizes.previewHeightRatio) * 100}% - 4px)`}
                    palette={palette}
                    textureCount={modelTextures.length}
                  />
                </div>
              </div>

              {/* Horizontal resize handle above texture strip */}
              <div
                className="resize-handle horizontal"
                onMouseDown={handleTextureStripResize}
              />

              {/* Bottom - Texture Strip */}
              <TextureStrip
                height={panelSizes.textureStripHeight}
                modelTextures={modelTextures}
                selectedTextureIndex={selectedTextureIndex}
                onSelectTexture={setSelectedTextureIndex}
                editedTextures={editedTextures}
              />
            </div>
          )}
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <SaveModal
          skinName={skinName}
          setSkinName={setSkinName}
          isSaving={isSaving}
          saveError={saveError}
          onSave={handleSaveToVault}
          onClose={() => setShowSaveModal(false)}
        />
      )}
    </>
  )
}
