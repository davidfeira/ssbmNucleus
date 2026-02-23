import { useState, useEffect, useRef, useCallback } from 'react'
import { usePanelResize } from '../hooks/usePanelResize'
import { playSound, playHoverSound } from '../utils/sounds'
import { API_URL, BACKEND_URL } from '../config'
import './SkinCreator.css'

export default function SkinCreator({
  isOpen,
  onClose,
  selectedCharacter,
  onSkinCreatorChange,
  onRefresh,
  initialCostume
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
  const [isDrawing, setIsDrawing] = useState(false)
  const isDrawingRef = useRef(false) // Ref for interval callback access
  const lastDrawPos = useRef(null)

  // Drawing tools state
  const [activeTool, setActiveTool] = useState('pencil') // pencil, eraser, fill, eyedropper
  const [drawColor, setDrawColor] = useState('#ff0000')
  const [brushSize, setBrushSize] = useState(1)
  const [undoStack, setUndoStack] = useState([])
  const [redoStack, setRedoStack] = useState([])
  const maxUndoSteps = 50
  const textureImportRef = useRef(null)
  const [editedTextures, setEditedTextures] = useState({}) // { [index]: dataUrl }
  const editedTexturesRef = useRef({}) // Ref for interval callback access
  const [isDirty, setIsDirty] = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [skinName, setSkinName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [viewerDragging, setViewerDragging] = useState(false)
  const [viewerDragButton, setViewerDragButton] = useState(null)
  const viewerLastMousePos = useRef({ x: 0, y: 0 })
  const [skinCreatorReconnecting, setSkinCreatorReconnecting] = useState(false)
  const [skinCreatorReconnectAttempts, setSkinCreatorReconnectAttempts] = useState(0)
  const skinCreatorReconnectTimeoutRef = useRef(null)
  const skinCreatorMaxReconnectAttempts = 3

  // Connection health and auto-refresh
  const autoRefreshIntervalRef = useRef(null)
  const pingIntervalRef = useRef(null)
  const lastMessageTimeRef = useRef(Date.now()) // Track last message received (any type)
  const [connectionFailed, setConnectionFailed] = useState(false)

  // Color Palette state
  const [colorPaletteEnabled, setColorPaletteEnabled] = useState(false)
  const [colorGroups, setColorGroups] = useState([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [maxColorGroups, setMaxColorGroups] = useState(8)
  const [selectedColorGroup, setSelectedColorGroup] = useState(null)
  const [originalTextureData, setOriginalTextureData] = useState({}) // { [index]: ImageData }
  const pixelGroupMapRef = useRef({}) // Maps pixels to their color group index
  const colorDebounceRef = useRef(null)
  const exportDatResolverRef = useRef(null) // For promise-based exportDat with Electron IPC

  // Panel resize hook
  const {
    sizes: panelSizes,
    handleRightPanelResize,
    handleTextureStripResize,
    handlePreviewResize,
  } = usePanelResize()

  // Canvas container sizing for dynamic scaling
  const canvasContainerRef = useRef(null)
  const [canvasContainerSize, setCanvasContainerSize] = useState({ width: 600, height: 600 })

  // Keep editedTexturesRef in sync with state for interval callback access
  useEffect(() => {
    editedTexturesRef.current = editedTextures
  }, [editedTextures])

  // Notify parent when skin creator opens/closes
  useEffect(() => {
    onSkinCreatorChange?.(isOpen)
  }, [isOpen, onSkinCreatorChange])

  // ResizeObserver for canvas container
  useEffect(() => {
    const container = canvasContainerRef.current
    if (!container) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setCanvasContainerSize({ width, height })
      }
    })

    resizeObserver.observe(container)
    return () => resizeObserver.disconnect()
  }, [skinCreatorStep])

  // Helper to update canvas scale based on container size
  const updateCanvasScale = useCallback((canvas, textureWidth, textureHeight) => {
    if (!canvas || !textureWidth || !textureHeight) return

    const padding = 40
    const availableWidth = canvasContainerSize.width - padding
    const availableHeight = canvasContainerSize.height - padding

    if (availableWidth <= 0 || availableHeight <= 0) return

    const scaleX = availableWidth / textureWidth
    const scaleY = availableHeight / textureHeight
    const scale = Math.min(scaleX, scaleY, 10)

    canvas.style.transform = `scale(${scale})`
    canvas.style.transformOrigin = 'center center'
  }, [canvasContainerSize])

  // Re-scale canvas when container size changes
  useEffect(() => {
    if (selectedTextureIndex === null || !modelTextures[selectedTextureIndex]) return
    const tex = modelTextures[selectedTextureIndex]
    const canvas = paintCanvasRef.current
    if (canvas && tex) {
      updateCanvasScale(canvas, tex.width, tex.height)
    }
  }, [canvasContainerSize, selectedTextureIndex, modelTextures, updateCanvasScale])

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

  // Check if Electron API is available
  const hasElectron = typeof window !== 'undefined' && window.electron?.viewerStart

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
    }
  }

  // Start viewer with selected costume (Electron IPC)
  const startSkinCreatorViewer = async (costume) => {
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

      // Set up message listener
      const cleanup = window.electron.onViewerMessage(handleViewerMessage)
      setViewerWs({ cleanup }) // Store cleanup function

      // Start embedded viewer via Electron IPC
      await window.electron.viewerStart({
        datFile: data.datFile,
        sceneFile: data.sceneFile,
        ajFile: data.ajFile,
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
  const startSkinCreatorFromVault = async (costume) => {
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

      // Set up message listener
      console.log('[SkinCreator] Setting up message listener for vault...')
      const cleanup = window.electron.onViewerMessage(handleViewerMessage)
      setViewerWs({ cleanup }) // Store cleanup function

      // Start embedded viewer via Electron IPC
      console.log('[SkinCreator] Calling viewerStart with paths:', data)
      const result = await window.electron.viewerStart({
        datFile: data.datFile,
        sceneFile: data.sceneFile,
        ajFile: data.ajFile,
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
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to close?')
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
    setColorPaletteEnabled(false)
    setColorGroups([])
    setOriginalTextureData({})
    pixelGroupMapRef.current = {}

    onClose?.()
  }

  // Camera controls (Electron IPC)
  const sendViewerCamera = (deltas) => {
    if (hasElectron && viewerWs) {
      window.electron.viewerCamera(
        deltas.deltaRotX || 0,
        deltas.deltaRotY || 0,
        deltas.deltaZoom || 0,
        deltas.deltaX || 0,
        deltas.deltaY || 0
      )
    }
  }

  const handleViewerMouseDown = (e) => {
    e.preventDefault()
    setViewerDragging(true)
    setViewerDragButton(e.button)
    viewerLastMousePos.current = { x: e.clientX, y: e.clientY }
  }

  const handleViewerMouseMove = (e) => {
    if (!viewerDragging) return

    const deltaX = e.clientX - viewerLastMousePos.current.x
    const deltaY = e.clientY - viewerLastMousePos.current.y
    viewerLastMousePos.current = { x: e.clientX, y: e.clientY }

    if (viewerDragButton === 2) {
      sendViewerCamera({ deltaX: -deltaX * 0.1, deltaY: deltaY * 0.1 })
    } else {
      sendViewerCamera({ deltaRotX: deltaY * 0.5, deltaRotY: deltaX * 0.5 })
    }
  }

  const handleViewerMouseUp = () => {
    setViewerDragging(false)
    setViewerDragButton(null)
  }

  const handleViewerWheel = (e) => {
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? -0.1 : 0.1
    sendViewerCamera({ deltaZoom: zoomFactor })
  }

  const handleViewerContextMenu = (e) => {
    e.preventDefault()
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

  // Update embedded viewer window position to match the 3D preview container
  const updateViewerPosition = useCallback(() => {
    if (!skinCreatorCanvasRef.current || !hasElectron) return

    const rect = skinCreatorCanvasRef.current.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1

    // Screen position = window position + element offset within window
    // On Windows, screenX/Y may have negative values for window chrome, so we use screenLeft/Top
    const screenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX
    const screenTop = window.screenTop !== undefined ? window.screenTop : window.screenY

    // Account for Electron window chrome (title bar height)
    const chromeHeight = window.outerHeight - window.innerHeight

    // All values above are CSS pixels - multiply by devicePixelRatio to get
    // physical pixels for Win32 SetWindowPos used by HSDRawViewer
    const x = Math.round((screenLeft + rect.left) * dpr)
    const y = Math.round((screenTop + chromeHeight + rect.top) * dpr)
    const width = Math.round(rect.width * dpr)
    const height = Math.round(rect.height * dpr)

    window.electron.viewerResize(x, y, width, height)
  }, [hasElectron])

  // Keep viewer positioned when window moves/resizes
  useEffect(() => {
    if (!viewerWs || !hasElectron || skinCreatorStep !== 'edit') return

    const handleResize = () => updateViewerPosition()

    window.addEventListener('resize', handleResize)
    window.addEventListener('scroll', handleResize)

    // Also update periodically in case window moves (no good event for this)
    const intervalId = setInterval(updateViewerPosition, 500)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('scroll', handleResize)
      clearInterval(intervalId)
    }
  }, [viewerWs, hasElectron, skinCreatorStep, updateViewerPosition])

  // Update viewer position when panel sizes change
  useEffect(() => {
    if (viewerWs && hasElectron && skinCreatorStep === 'edit') {
      updateViewerPosition()
    }
  }, [panelSizes, viewerWs, hasElectron, skinCreatorStep, updateViewerPosition])

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

  // Undo/Redo functions
  const saveToUndoStack = () => {
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setUndoStack(prev => {
      const newStack = [...prev, imageData]
      if (newStack.length > maxUndoSteps) newStack.shift()
      return newStack
    })
    setRedoStack([]) // Clear redo stack on new action
  }

  const undo = () => {
    if (undoStack.length === 0) return
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    // Save current state to redo stack
    const currentState = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setRedoStack(prev => [...prev, currentState])

    // Restore previous state
    const previousState = undoStack[undoStack.length - 1]
    setUndoStack(prev => prev.slice(0, -1))
    ctx.putImageData(previousState, 0, 0)
    sendTextureUpdate()
  }

  const redo = () => {
    if (redoStack.length === 0) return
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    // Save current state to undo stack
    const currentState = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setUndoStack(prev => [...prev, currentState])

    // Restore next state
    const nextState = redoStack[redoStack.length - 1]
    setRedoStack(prev => prev.slice(0, -1))
    ctx.putImageData(nextState, 0, 0)
    sendTextureUpdate()
  }

  // Clear undo/redo when switching textures
  useEffect(() => {
    setUndoStack([])
    setRedoStack([])
  }, [selectedTextureIndex])

  // Keyboard shortcuts for undo/redo
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen || skinCreatorStep !== 'edit') return
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'z' && !e.shiftKey) {
          e.preventDefault()
          undo()
        } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
          e.preventDefault()
          redo()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, skinCreatorStep, undoStack, redoStack])

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

  // Paint canvas mouse handlers
  const getCanvasCoords = (e) => {
    const canvas = paintCanvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return {
      x: Math.floor((e.clientX - rect.left) * scaleX),
      y: Math.floor((e.clientY - rect.top) * scaleY)
    }
  }

  const drawBrush = (x, y, color, size = brushSize) => {
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = color

    if (size === 1) {
      ctx.fillRect(x, y, 1, 1)
    } else {
      // Draw a square brush centered on the point
      const offset = Math.floor(size / 2)
      for (let dy = 0; dy < size; dy++) {
        for (let dx = 0; dx < size; dx++) {
          const px = x - offset + dx
          const py = y - offset + dy
          if (px >= 0 && px < canvas.width && py >= 0 && py < canvas.height) {
            ctx.fillRect(px, py, 1, 1)
          }
        }
      }
    }
  }

  const eraseBrush = (x, y, size = brushSize) => {
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const offset = Math.floor(size / 2)
    for (let dy = 0; dy < size; dy++) {
      for (let dx = 0; dx < size; dx++) {
        const px = x - offset + dx
        const py = y - offset + dy
        if (px >= 0 && px < canvas.width && py >= 0 && py < canvas.height) {
          ctx.clearRect(px, py, 1, 1)
        }
      }
    }
  }

  const drawLine = (x0, y0, x1, y1, toolFn) => {
    const dx = Math.abs(x1 - x0)
    const dy = Math.abs(y1 - y0)
    const sx = x0 < x1 ? 1 : -1
    const sy = y0 < y1 ? 1 : -1
    let err = dx - dy

    while (true) {
      toolFn(x0, y0)
      if (x0 === x1 && y0 === y1) break
      const e2 = 2 * err
      if (e2 > -dy) { err -= dy; x0 += sx }
      if (e2 < dx) { err += dx; y0 += sy }
    }
  }

  const floodFill = (startX, startY, fillColor) => {
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data
    const width = canvas.width
    const height = canvas.height

    // Parse fill color
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = tempCanvas.height = 1
    const tempCtx = tempCanvas.getContext('2d')
    tempCtx.fillStyle = fillColor
    tempCtx.fillRect(0, 0, 1, 1)
    const fillRgba = tempCtx.getImageData(0, 0, 1, 1).data

    // Get target color
    const startIdx = (startY * width + startX) * 4
    const targetR = data[startIdx]
    const targetG = data[startIdx + 1]
    const targetB = data[startIdx + 2]
    const targetA = data[startIdx + 3]

    // Don't fill if same color
    if (targetR === fillRgba[0] && targetG === fillRgba[1] &&
        targetB === fillRgba[2] && targetA === fillRgba[3]) return

    const stack = [[startX, startY]]
    const visited = new Set()

    while (stack.length > 0) {
      const [x, y] = stack.pop()
      const key = `${x},${y}`

      if (visited.has(key)) continue
      if (x < 0 || x >= width || y < 0 || y >= height) continue

      const idx = (y * width + x) * 4
      if (data[idx] !== targetR || data[idx + 1] !== targetG ||
          data[idx + 2] !== targetB || data[idx + 3] !== targetA) continue

      visited.add(key)
      data[idx] = fillRgba[0]
      data[idx + 1] = fillRgba[1]
      data[idx + 2] = fillRgba[2]
      data[idx + 3] = fillRgba[3]

      stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1])
    }

    ctx.putImageData(imageData, 0, 0)
  }

  const eyedropperPick = (x, y) => {
    const canvas = paintCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const pixel = ctx.getImageData(x, y, 1, 1).data
    const hex = '#' + [pixel[0], pixel[1], pixel[2]]
      .map(c => c.toString(16).padStart(2, '0')).join('')
    setDrawColor(hex)
    setActiveTool('pencil') // Switch back to pencil after picking
  }

  const handlePaintMouseDown = (e) => {
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const coords = getCanvasCoords(e)
    if (!coords) return

    if (activeTool === 'eyedropper') {
      eyedropperPick(coords.x, coords.y)
      return
    }

    if (activeTool === 'fill') {
      saveToUndoStack()
      floodFill(coords.x, coords.y, drawColor)
      sendTextureUpdate()
      return
    }

    // Pencil or eraser - start drawing
    saveToUndoStack()
    setIsDrawing(true)
    isDrawingRef.current = true

    if (activeTool === 'pencil') {
      drawBrush(coords.x, coords.y, drawColor)
    } else if (activeTool === 'eraser') {
      eraseBrush(coords.x, coords.y)
    }
    lastDrawPos.current = coords
  }

  const handlePaintMouseMove = (e) => {
    if (!isDrawing) return
    const coords = getCanvasCoords(e)
    if (!coords) return

    const toolFn = activeTool === 'eraser'
      ? (x, y) => eraseBrush(x, y)
      : (x, y) => drawBrush(x, y, drawColor)

    if (lastDrawPos.current) {
      drawLine(lastDrawPos.current.x, lastDrawPos.current.y, coords.x, coords.y, toolFn)
    } else {
      toolFn(coords.x, coords.y)
    }
    lastDrawPos.current = coords
  }

  const handlePaintMouseUp = () => {
    if (isDrawing) {
      setIsDrawing(false)
      isDrawingRef.current = false
      lastDrawPos.current = null
      sendTextureUpdate()
    }
  }

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

  // Color utility functions
  const rgbToHsl = (r, g, b) => {
    r /= 255; g /= 255; b /= 255
    const max = Math.max(r, g, b)
    const min = Math.min(r, g, b)
    let h, s, l = (max + min) / 2

    if (max === min) {
      h = s = 0
    } else {
      const d = max - min
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
        case g: h = ((b - r) / d + 2) / 6; break
        case b: h = ((r - g) / d + 4) / 6; break
        default: h = 0
      }
    }
    return { h: h * 360, s: s * 100, l: l * 100 }
  }

  const hslToRgb = (h, s, l) => {
    h /= 360; s /= 100; l /= 100
    let r, g, b

    if (s === 0) {
      r = g = b = l
    } else {
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1
        if (t > 1) t -= 1
        if (t < 1/6) return p + (q - p) * 6 * t
        if (t < 1/2) return q
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
        return p
      }
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s
      const p = 2 * l - q
      r = hue2rgb(p, q, h + 1/3)
      g = hue2rgb(p, q, h)
      b = hue2rgb(p, q, h - 1/3)
    }
    return {
      r: Math.round(r * 255),
      g: Math.round(g * 255),
      b: Math.round(b * 255)
    }
  }

  // Analyze all textures and detect color groups
  const analyzeColors = async () => {
    if (modelTextures.length === 0) return
    setIsAnalyzing(true)

    try {
      // First, capture original texture data
      const originals = {}
      for (let texIdx = 0; texIdx < modelTextures.length; texIdx++) {
        const tex = modelTextures[texIdx]
        const imgSrc = editedTextures[texIdx] || (tex.thumbnail ? `data:image/png;base64,${tex.thumbnail}` : null)
        if (!imgSrc) continue

        const img = await new Promise((resolve) => {
          const i = new Image()
          i.onload = () => resolve(i)
          i.src = imgSrc
        })

        const canvas = document.createElement('canvas')
        canvas.width = tex.width
        canvas.height = tex.height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, tex.width, tex.height)
        originals[texIdx] = ctx.getImageData(0, 0, tex.width, tex.height)
      }
      setOriginalTextureData(originals)

      // Collect all pixels with their HSL values
      const HUE_TOLERANCE = 25
      const hueBins = new Array(360).fill(null).map(() => ({ count: 0, totalS: 0, totalL: 0 }))

      for (const texIdx of Object.keys(originals)) {
        const imageData = originals[texIdx]
        const { data } = imageData

        for (let i = 0; i < data.length; i += 4) {
          const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3]
          if (a < 128) continue // Skip transparent

          const hsl = rgbToHsl(r, g, b)
          if (hsl.l < 10 || hsl.l > 90) continue // Skip near black/white
          if (hsl.s < 15) continue // Skip grays

          const hueIdx = Math.floor(hsl.h) % 360
          hueBins[hueIdx].count++
          hueBins[hueIdx].totalS += hsl.s
          hueBins[hueIdx].totalL += hsl.l
        }
      }

      // Merge adjacent hue bins into groups
      const rawGroups = []
      let currentGroup = null

      for (let h = 0; h < 360; h++) {
        const bin = hueBins[h]
        if (bin.count > 0) {
          if (!currentGroup) {
            currentGroup = { startHue: h, endHue: h, count: bin.count, totalS: bin.totalS, totalL: bin.totalL }
          } else if (h - currentGroup.endHue <= HUE_TOLERANCE) {
            currentGroup.endHue = h
            currentGroup.count += bin.count
            currentGroup.totalS += bin.totalS
            currentGroup.totalL += bin.totalL
          } else {
            if (currentGroup.count >= 100) rawGroups.push(currentGroup)
            currentGroup = { startHue: h, endHue: h, count: bin.count, totalS: bin.totalS, totalL: bin.totalL }
          }
        }
      }
      if (currentGroup && currentGroup.count >= 100) rawGroups.push(currentGroup)

      // Handle wrap-around (red at 0 and 360)
      if (rawGroups.length >= 2) {
        const first = rawGroups[0]
        const last = rawGroups[rawGroups.length - 1]
        if (first.startHue < HUE_TOLERANCE && last.endHue > 360 - HUE_TOLERANCE) {
          // Merge last into first
          first.startHue = last.startHue - 360
          first.count += last.count
          first.totalS += last.totalS
          first.totalL += last.totalL
          rawGroups.pop()
        }
      }

      // Adjust groups to exactly match maxColorGroups
      // Merge if too many, split if too few

      // Merge closest groups if we have too many
      while (rawGroups.length > maxColorGroups) {
        let minDist = Infinity
        let mergeI = 0, mergeJ = 1

        for (let i = 0; i < rawGroups.length; i++) {
          for (let j = i + 1; j < rawGroups.length; j++) {
            const g1 = rawGroups[i]
            const g2 = rawGroups[j]
            const hue1 = ((g1.startHue + g1.endHue) / 2 + 360) % 360
            const hue2 = ((g2.startHue + g2.endHue) / 2 + 360) % 360
            let dist = Math.abs(hue1 - hue2)
            if (dist > 180) dist = 360 - dist
            if (dist < minDist) {
              minDist = dist
              mergeI = i
              mergeJ = j
            }
          }
        }

        const gi = rawGroups[mergeI]
        const gj = rawGroups[mergeJ]
        gi.startHue = Math.min(gi.startHue, gj.startHue)
        gi.endHue = Math.max(gi.endHue, gj.endHue)
        gi.count += gj.count
        gi.totalS += gj.totalS
        gi.totalL += gj.totalL
        rawGroups.splice(mergeJ, 1)
      }

      // Split largest groups if we have too few
      while (rawGroups.length < maxColorGroups && rawGroups.length > 0) {
        // Find the group with the widest hue range to split
        let maxRange = -1
        let splitIdx = 0
        for (let i = 0; i < rawGroups.length; i++) {
          const g = rawGroups[i]
          const range = g.endHue - g.startHue
          if (range > maxRange) {
            maxRange = range
            splitIdx = i
          }
        }

        const g = rawGroups[splitIdx]
        if (g.endHue - g.startHue < 2) {
          // Can't split further, just duplicate with slight offset
          break
        }

        const midHue = Math.floor((g.startHue + g.endHue) / 2)

        // Create two new groups from the split
        const g1 = {
          startHue: g.startHue,
          endHue: midHue,
          count: Math.floor(g.count / 2),
          totalS: g.totalS / 2,
          totalL: g.totalL / 2
        }
        const g2 = {
          startHue: midHue + 1,
          endHue: g.endHue,
          count: Math.ceil(g.count / 2),
          totalS: g.totalS / 2,
          totalL: g.totalL / 2
        }

        rawGroups.splice(splitIdx, 1, g1, g2)
      }

      // Sort by pixel count for consistent ordering
      rawGroups.sort((a, b) => b.count - a.count)

      // Convert to color group objects
      const groups = rawGroups.map((g, idx) => {
        const avgS = g.totalS / g.count
        const avgL = g.totalL / g.count
        const centerHue = ((g.startHue + g.endHue) / 2 + 360) % 360
        return {
          id: `group-${idx}`,
          centerHue,
          hueRange: [(g.startHue + 360) % 360, g.endHue % 360],
          pixelCount: g.count,
          displayColor: `hsl(${Math.round(centerHue)}, ${Math.round(avgS)}%, ${Math.round(avgL)}%)`,
          avgSaturation: avgS,
          avgLightness: avgL,
          hueShift: 0,
          saturationShift: 0
        }
      })

      // Build pixel-to-group map for each texture
      const pixelMap = {}
      for (const texIdx of Object.keys(originals)) {
        const imageData = originals[texIdx]
        const { data, width, height } = imageData
        const map = new Uint8Array(width * height).fill(255)

        for (let i = 0; i < data.length; i += 4) {
          const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3]
          if (a < 128) continue

          const hsl = rgbToHsl(r, g, b)
          if (hsl.l < 10 || hsl.l > 90) continue
          if (hsl.s < 15) continue

          const pixelHue = hsl.h
          for (let gIdx = 0; gIdx < groups.length; gIdx++) {
            const group = groups[gIdx]
            let inRange = false
            if (group.hueRange[0] <= group.hueRange[1]) {
              inRange = pixelHue >= group.hueRange[0] - HUE_TOLERANCE && pixelHue <= group.hueRange[1] + HUE_TOLERANCE
            } else {
              // Wraps around 0
              inRange = pixelHue >= group.hueRange[0] - HUE_TOLERANCE || pixelHue <= group.hueRange[1] + HUE_TOLERANCE
            }
            if (inRange) {
              map[i / 4] = gIdx
              break
            }
          }
        }
        pixelMap[texIdx] = map
      }
      pixelGroupMapRef.current = pixelMap

      setColorGroups(groups)
      setColorPaletteEnabled(true)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Apply color adjustments to all textures
  const applyColorAdjustments = (groups) => {
    if (!groups || groups.length === 0 || Object.keys(originalTextureData).length === 0) return

    // Skip if all adjustments are zero
    const hasAdjustments = groups.some(g => g.hueShift !== 0 || g.saturationShift !== 0)
    if (!hasAdjustments) return

    const newEditedTextures = { ...editedTextures }

    for (const texIdxStr of Object.keys(originalTextureData)) {
      const texIdx = parseInt(texIdxStr)
      const original = originalTextureData[texIdx]
      const pixelMap = pixelGroupMapRef.current[texIdx]
      if (!original || !pixelMap) continue

      const result = new ImageData(
        new Uint8ClampedArray(original.data),
        original.width,
        original.height
      )

      for (let i = 0; i < result.data.length; i += 4) {
        const pixelIdx = i / 4
        const groupIdx = pixelMap[pixelIdx]
        if (groupIdx === 255) continue

        const group = groups[groupIdx]
        if (!group || (group.hueShift === 0 && group.saturationShift === 0)) continue

        const r = original.data[i]
        const g = original.data[i + 1]
        const b = original.data[i + 2]

        const hsl = rgbToHsl(r, g, b)
        let newH = (hsl.h + group.hueShift + 360) % 360
        let newS = Math.max(0, Math.min(100, hsl.s + group.saturationShift))

        const newRgb = hslToRgb(newH, newS, hsl.l)
        result.data[i] = newRgb.r
        result.data[i + 1] = newRgb.g
        result.data[i + 2] = newRgb.b
      }

      // Convert to data URL
      const canvas = document.createElement('canvas')
      canvas.width = original.width
      canvas.height = original.height
      const ctx = canvas.getContext('2d')
      ctx.putImageData(result, 0, 0)
      newEditedTextures[texIdx] = canvas.toDataURL('image/png')

      // Send to viewer via Electron IPC
      if (hasElectron && viewerWs) {
        const base64 = newEditedTextures[texIdx].replace('data:image/png;base64,', '')
        window.electron.viewerSend({
          type: 'updateTexture',
          index: texIdx,
          data: base64
        })
      }
    }

    setEditedTextures(newEditedTextures)
    setIsDirty(true)
  }

  // Handle color group adjustment
  const handleColorAdjust = (groupId, field, value) => {
    setColorGroups(prev => prev.map(g => {
      if (g.id !== groupId) return g
      if (field === 'reset') {
        return { ...g, hueShift: 0, saturationShift: 0 }
      }
      return { ...g, [field]: value }
    }))
  }

  // Apply color adjustments when groups change (debounced via effect)
  useEffect(() => {
    if (!colorPaletteEnabled || colorGroups.length === 0) return

    // Debounce the application
    if (colorDebounceRef.current) {
      clearTimeout(colorDebounceRef.current)
    }
    colorDebounceRef.current = setTimeout(() => {
      applyColorAdjustments(colorGroups)
    }, 50)

    return () => {
      if (colorDebounceRef.current) {
        clearTimeout(colorDebounceRef.current)
      }
    }
  }, [colorGroups, colorPaletteEnabled])

  // Reset color palette
  const resetColorPalette = () => {
    setColorPaletteEnabled(false)
    setColorGroups([])
    setSelectedColorGroup(null)
    setOriginalTextureData({})
    pixelGroupMapRef.current = {}
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
      const datPromise = new Promise((resolve, reject) => {
        exportDatResolverRef.current = { resolve, reject }
        window.electron.viewerSend({ type: 'exportDat' })

        setTimeout(() => {
          if (exportDatResolverRef.current) {
            exportDatResolverRef.current = null
            reject(new Error('Export timed out'))
          }
        }, 30000)
      })

      const base64Data = await datPromise

      const byteCharacters = atob(base64Data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const datBlob = new Blob([byteArray], { type: 'application/octet-stream' })

      const { default: JSZip } = await import('jszip')
      const zip = new JSZip()
      zip.file(`${skinName.trim()}.dat`, datBlob)
      const zipBlob = await zip.generateAsync({ type: 'blob' })

      const formData = new FormData()
      formData.append('file', new File([zipBlob], `${skinName.trim()}.zip`))
      formData.append('custom_title', skinName.trim())

      const response = await fetch(`${API_URL}/import/file`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Import failed')
      }

      setShowSaveModal(false)
      setIsDirty(false)
      setSkinName('')

      onRefresh?.()

      playSound('newSkin')
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
      const datPromise = new Promise((resolve, reject) => {
        exportDatResolverRef.current = { resolve, reject }
        window.electron.viewerSend({ type: 'exportDat' })

        setTimeout(() => {
          if (exportDatResolverRef.current) {
            exportDatResolverRef.current = null
            reject(new Error('Export timed out'))
          }
        }, 30000)
      })

      const base64Data = await datPromise

      const byteCharacters = atob(base64Data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const datBlob = new Blob([byteArray], { type: 'application/octet-stream' })

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
            <div className="skin-creator-header">
              <div className="skin-creator-title">
                <h1>Skin Creator</h1>
                <span className="skin-creator-character">{selectedCharacter}</span>
                {selectedVanillaCostume && (
                  <span className="skin-creator-costume">{selectedVanillaCostume.colorName}</span>
                )}
                {isDirty && <span className="skin-creator-dirty">*</span>}
              </div>
              <div className="skin-creator-header-buttons">
                <button
                  className="skin-creator-save"
                  onClick={openSaveModal}
                  title="Save to Vault"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                    <polyline points="7 3 7 8 15 8"></polyline>
                  </svg>
                  <span>Save</span>
                </button>
                <button
                  className="skin-creator-export"
                  onClick={handleDownloadDat}
                  title="Download DAT file"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
                  <span>Download</span>
                </button>
                <button
                  className="skin-creator-close"
                  onClick={() => closeSkinCreator()}
                  title="Close (Esc)"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                  <span>Close</span>
                </button>
              </div>
            </div>
          )}

          {/* Costume Selection Step */}
          {skinCreatorStep === 'select' && (
            <div className="skin-creator-select">
              {initialCostume ? (
                <div className="skin-creator-loading-edit">
                  <div className="loading-spinner"></div>
                  <span>Loading skin editor...</span>
                </div>
              ) : (
              <div className="skin-creator-select-content">
                <div className="skin-creator-select-header">
                  <button
                    className="back-button"
                    onClick={() => closeSkinCreator()}
                  >
                    ← Back
                  </button>
                </div>
                <h2>Select a base costume</h2>
                <p>Choose a vanilla costume to use as your starting point</p>

              {skinCreatorLoading && (
                <div className="skin-creator-loading">Loading costumes...</div>
              )}

              {skinCreatorReconnecting && (
                <div className="skin-creator-reconnecting">
                  Reconnecting... (attempt {skinCreatorReconnectAttempts}/{skinCreatorMaxReconnectAttempts})
                </div>
              )}

              {skinCreatorError && skinCreatorError !== 'closing' && (
                <div className="skin-creator-error">{skinCreatorError}</div>
              )}

              <div className="skin-creator-costume-grid">
                {vanillaCostumes.map(costume => (
                  <div
                    key={costume.code}
                    className="skin-creator-costume-card"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); startSkinCreatorViewer(costume); }}
                  >
                    <div className="costume-preview">
                      {costume.hasCsp ? (
                        <img
                          src={`${BACKEND_URL}/vanilla/${selectedCharacter}/${costume.code}/csp.png`}
                          alt={costume.colorName}
                        />
                      ) : (
                        <div className="costume-placeholder">{costume.colorCode}</div>
                      )}
                    </div>
                    <div className="costume-name">{costume.colorName}</div>
                  </div>
                ))}
              </div>
              </div>
              )}
            </div>
          )}

          {/* Editor Step */}
          {skinCreatorStep === 'edit' && (
            <div className="skin-creator-body">
              {/* Main area: Canvas + Right Panel */}
              <div className="skin-creator-main">
                {/* Center - Paint Canvas */}
                <div className="skin-creator-canvas-area">
                  <div className="skin-creator-toolbar">
                    {/* Undo/Redo */}
                    <button
                      className="toolbar-btn"
                      onClick={undo}
                      disabled={undoStack.length === 0}
                      title="Undo (Ctrl+Z)"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>
                      </svg>
                    </button>
                    <button
                      className="toolbar-btn"
                      onClick={redo}
                      disabled={redoStack.length === 0}
                      title="Redo (Ctrl+Y)"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"/>
                      </svg>
                    </button>

                    <div className="toolbar-separator"></div>

                    {/* Color Picker */}
                    <div className="color-picker-wrapper">
                      <input
                        type="color"
                        className="color-picker"
                        value={drawColor}
                        onChange={(e) => setDrawColor(e.target.value)}
                        title="Draw Color"
                      />
                    </div>

                    <div className="toolbar-separator"></div>

                    {/* Tools */}
                    <button
                      className={`toolbar-btn ${activeTool === 'pencil' ? 'active' : ''}`}
                      onClick={() => setActiveTool('pencil')}
                      title="Pencil (draw)"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                      </svg>
                    </button>
                    <button
                      className={`toolbar-btn ${activeTool === 'eraser' ? 'active' : ''}`}
                      onClick={() => setActiveTool('eraser')}
                      title="Eraser"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/>
                        <path d="M22 21H7"/><path d="m5 11 9 9"/>
                      </svg>
                    </button>
                    <button
                      className={`toolbar-btn ${activeTool === 'fill' ? 'active' : ''}`}
                      onClick={() => setActiveTool('fill')}
                      title="Fill Bucket"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="m19 11-8-8-8.6 8.6a2 2 0 0 0 0 2.8l5.2 5.2c.8.8 2 .8 2.8 0L19 11Z"/>
                        <path d="m5 2 5 5"/><path d="M2 13h15"/><path d="M22 20a2 2 0 1 1-4 0c0-1.6 1.7-2.4 2-4 .3 1.6 2 2.4 2 4Z"/>
                      </svg>
                    </button>
                    <button
                      className={`toolbar-btn ${activeTool === 'eyedropper' ? 'active' : ''}`}
                      onClick={() => setActiveTool('eyedropper')}
                      title="Eyedropper (pick color)"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="m2 22 1-1h3l9-9"/><path d="M3 21v-3l9-9"/>
                        <path d="m15 6 3.4-3.4a2.1 2.1 0 1 1 3 3L18 9l.4.4a2.1 2.1 0 1 1-3 3l-3.8-3.8a2.1 2.1 0 1 1 3-3l.4.4Z"/>
                      </svg>
                    </button>

                    <div className="toolbar-separator"></div>

                    {/* Brush Size */}
                    <span className="toolbar-label">Size:</span>
                    <input
                      type="range"
                      className="brush-size-slider"
                      min="1"
                      max="20"
                      value={brushSize}
                      onChange={(e) => setBrushSize(parseInt(e.target.value))}
                      title="Brush Size"
                    />
                    <span className="brush-size-value">{brushSize}</span>
                  </div>
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
                        <div className="canvas-floating-actions">
                          <input
                            ref={textureImportRef}
                            type="file"
                            accept="image/png,image/jpeg,image/gif"
                            style={{ display: 'none' }}
                            onChange={importTexture}
                          />
                          <button
                            className="canvas-float-btn"
                            onClick={() => textureImportRef.current?.click()}
                            title="Import texture from file"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                              <polyline points="17 8 12 3 7 8"/>
                              <line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                            Import
                          </button>
                          <button
                            className="canvas-float-btn"
                            onClick={exportTexture}
                            title="Export texture as PNG"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                              <polyline points="7 10 12 15 17 10"/>
                              <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Export
                          </button>
                        </div>
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
                  <div className="skin-creator-tool-palette" style={{ height: `calc(${(1 - panelSizes.previewHeightRatio) * 100}% - 4px)` }}>
                    <div className="skin-creator-panel-header">Tools</div>
                    <div className="tool-palette-content">
                      {/* Batch Tools (Color Palette) */}
                      <div className="tool-section">
                        <div className="tool-section-header">
                          <span className="tool-section-title">
                            Batch Operations
                            <span className="tool-section-badge batch">All Textures</span>
                          </span>
                        </div>
                        <div className="tool-section-content">
                          {/* Color Palette */}
                          <div className="tool-palette-section-header">
                            <span className="tool-palette-section-title">Color Palette</span>
                            <div className="palette-controls">
                              {!colorPaletteEnabled && (
                                <input
                                  type="number"
                                  className="max-groups-input"
                                  min="2"
                                  max="16"
                                  value={maxColorGroups}
                                  onChange={(e) => setMaxColorGroups(Math.min(16, Math.max(2, parseInt(e.target.value) || 8)))}
                                  title="Max color groups"
                                />
                              )}
                              {!colorPaletteEnabled ? (
                                <button
                                  className="palette-analyze-btn"
                                  onClick={analyzeColors}
                                  disabled={isAnalyzing || modelTextures.length === 0}
                                >
                                  {isAnalyzing ? 'Analyzing...' : 'Analyze'}
                                </button>
                              ) : (
                                <button
                                  className="palette-reset-btn"
                                  onClick={resetColorPalette}
                                  title="Reset color adjustments"
                                >
                                  Reset
                                </button>
                              )}
                            </div>
                          </div>

                          {isAnalyzing && (
                            <div className="palette-loading">
                              Analyzing textures...
                            </div>
                          )}

                          {colorPaletteEnabled && colorGroups.length > 0 && (
                            <>
                              {/* Color Grid */}
                              <div className="color-grid">
                                {colorGroups.map(group => {
                                  const isSelected = selectedColorGroup === group.id
                                  const hasChanges = group.hueShift !== 0 || group.saturationShift !== 0
                                  const currentColor = `hsl(${(group.centerHue + group.hueShift + 360) % 360}, ${Math.max(0, Math.min(100, group.avgSaturation + group.saturationShift))}%, ${group.avgLightness}%)`
                                  return (
                                    <div
                                      key={group.id}
                                      className={`color-grid-item ${isSelected ? 'selected' : ''} ${hasChanges ? 'modified' : ''}`}
                                      onClick={() => setSelectedColorGroup(isSelected ? null : group.id)}
                                      title={`${group.pixelCount > 1000 ? `${(group.pixelCount / 1000).toFixed(1)}k` : group.pixelCount} pixels`}
                                    >
                                      <div className="color-grid-swatch" style={{ background: currentColor }} />
                                      {hasChanges && <div className="color-grid-original" style={{ background: group.displayColor }} />}
                                    </div>
                                  )
                                })}
                              </div>

                              {/* Expanded Controls for Selected Color */}
                              {selectedColorGroup && colorGroups.find(g => g.id === selectedColorGroup) && (() => {
                                const group = colorGroups.find(g => g.id === selectedColorGroup)
                                return (
                                  <div className="color-editor">
                                    <div className="color-editor-header">
                                      <div className="color-editor-swatches">
                                        <div className="color-swatch-original" style={{ background: group.displayColor }} />
                                        <span className="color-arrow">-></span>
                                        <div
                                          className="color-swatch"
                                          style={{
                                            background: `hsl(${(group.centerHue + group.hueShift + 360) % 360}, ${Math.max(0, Math.min(100, group.avgSaturation + group.saturationShift))}%, ${group.avgLightness}%)`
                                          }}
                                        />
                                      </div>
                                      <button
                                        className="color-reset-btn"
                                        onClick={() => handleColorAdjust(group.id, 'reset', 0)}
                                        disabled={group.hueShift === 0 && group.saturationShift === 0}
                                      >
                                        Reset
                                      </button>
                                    </div>
                                    <div className="color-editor-sliders">
                                      <div className="slider-row">
                                        <label>Hue</label>
                                        <div
                                          className="slider-track"
                                          style={{
                                            background: `linear-gradient(to right,
                                              hsl(${(group.centerHue - 180 + 360) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue - 120 + 360) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue - 60 + 360) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${group.centerHue}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue + 60) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue + 120) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue + 180) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%))`
                                          }}
                                        >
                                          <input
                                            type="range"
                                            className="color-slider"
                                            min="-180"
                                            max="180"
                                            value={group.hueShift}
                                            onChange={(e) => handleColorAdjust(group.id, 'hueShift', parseInt(e.target.value))}
                                          />
                                          <div
                                            className="slider-thumb-indicator"
                                            style={{
                                              left: `${((group.hueShift + 180) / 360) * 100}%`,
                                              background: `hsl(${(group.centerHue + group.hueShift + 360) % 360}, ${group.avgSaturation}%, ${group.avgLightness}%)`
                                            }}
                                          />
                                        </div>
                                        <span className="slider-value">{group.hueShift > 0 ? '+' : ''}{group.hueShift}</span>
                                      </div>
                                      <div className="slider-row">
                                        <label>Sat</label>
                                        <div
                                          className="slider-track sat-track"
                                          style={{
                                            background: `linear-gradient(to right,
                                              hsl(${(group.centerHue + group.hueShift + 360) % 360}, 0%, ${group.avgLightness}%),
                                              hsl(${(group.centerHue + group.hueShift + 360) % 360}, 100%, ${group.avgLightness}%))`
                                          }}
                                        >
                                          <input
                                            type="range"
                                            className="color-slider"
                                            min="-100"
                                            max="100"
                                            value={group.saturationShift}
                                            onChange={(e) => handleColorAdjust(group.id, 'saturationShift', parseInt(e.target.value))}
                                          />
                                          <div
                                            className="slider-thumb-indicator"
                                            style={{
                                              left: `${((group.saturationShift + 100) / 200) * 100}%`,
                                              background: `hsl(${(group.centerHue + group.hueShift + 360) % 360}, ${Math.max(0, Math.min(100, group.avgSaturation + group.saturationShift))}%, ${group.avgLightness}%)`
                                            }}
                                          />
                                        </div>
                                        <span className="slider-value">{group.saturationShift > 0 ? '+' : ''}{group.saturationShift}</span>
                                      </div>
                                    </div>
                                  </div>
                                )
                              })()}
                            </>
                          )}

                          {colorPaletteEnabled && colorGroups.length === 0 && (
                            <div className="no-colors-found">
                              No color groups detected
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Horizontal resize handle above texture strip */}
              <div
                className="resize-handle horizontal"
                onMouseDown={handleTextureStripResize}
              />

              {/* Bottom - Texture Strip */}
              <div className="skin-creator-texture-strip" style={{ height: panelSizes.textureStripHeight }}>
                <div className="skin-creator-panel-header">Textures ({modelTextures.length})</div>
                <div className="skin-creator-texture-list">
                  {modelTextures.length === 0 ? (
                    <div className="texture-loading">Loading textures...</div>
                  ) : (
                    modelTextures.map((tex, idx) => (
                      <div
                        key={idx}
                        className={`skin-creator-texture-item ${selectedTextureIndex === idx ? 'selected' : ''} ${editedTextures[idx] ? 'edited' : ''}`}
                        onClick={() => setSelectedTextureIndex(idx)}
                      >
                        <div className="texture-thumbnail">
                          {editedTextures[idx] ? (
                            <img
                              src={editedTextures[idx]}
                              alt={tex.name}
                              style={{
                                aspectRatio: `${tex.width} / ${tex.height}`
                              }}
                            />
                          ) : tex.thumbnail && (
                            <img
                              src={`data:image/png;base64,${tex.thumbnail}`}
                              alt={tex.name}
                              style={{
                                aspectRatio: `${tex.width} / ${tex.height}`
                              }}
                            />
                          )}
                        </div>
                        <div className="texture-info">
                          <span className="texture-name">{tex.name}{editedTextures[idx] && ' *'}</span>
                          <span className="texture-size">{tex.width}x{tex.height}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="skin-creator-save-overlay" onClick={() => !isSaving && setShowSaveModal(false)}>
          <div className="skin-creator-save-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Save to Vault</h2>
            <p>Enter a name for your custom skin:</p>
            <input
              type="text"
              className="skin-name-input"
              value={skinName}
              onChange={(e) => setSkinName(e.target.value)}
              placeholder="Skin name..."
              disabled={isSaving}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isSaving) handleSaveToVault()
                if (e.key === 'Escape' && !isSaving) setShowSaveModal(false)
              }}
            />
            {saveError && <div className="save-error">{saveError}</div>}
            <div className="save-modal-buttons">
              <button
                className="save-cancel"
                onClick={() => { playSound('back'); setShowSaveModal(false); }}
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                className="save-confirm"
                onClick={handleSaveToVault}
                disabled={isSaving || !skinName.trim()}
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
