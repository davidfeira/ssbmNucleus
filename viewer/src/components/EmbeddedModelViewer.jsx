import { useState, useEffect, useRef, useCallback } from 'react'
import './StorageViewer.css'  // Reuse existing modal styles

/**
 * Embedded 3D Model Viewer Component
 * Uses native HSDRawViewer window embedded via Electron IPC
 * No frame streaming - renders directly in OpenGL
 */

console.log('[EmbeddedModelViewer] Module loaded')

// Animation name mappings (same as ModelViewer.jsx)
const ANIM_NAMES = {
  'Attack11': 'Jab 1', 'Attack12': 'Jab 2', 'Attack13': 'Jab 3',
  'AttackHi3': 'Up Tilt', 'AttackLw3': 'Down Tilt', 'AttackS3S': 'Forward Tilt',
  'AttackHi4': 'Up Smash', 'AttackLw4': 'Down Smash', 'AttackS4S': 'Forward Smash',
  'AttackDash': 'Dash Attack',
  'AttackAirN': 'Neutral Air', 'AttackAirHi': 'Up Air', 'AttackAirF': 'Forward Air',
  'AttackAirLw': 'Down Air', 'AttackAirB': 'Back Air',
  'SpecialN': 'Neutral Special', 'SpecialHi': 'Up Special',
  'SpecialLw': 'Down Special', 'SpecialS': 'Side Special',
  'Catch': 'Grab', 'ThrowF': 'Forward Throw', 'ThrowB': 'Back Throw',
  'ThrowHi': 'Up Throw', 'ThrowLw': 'Down Throw',
  'Wait1': 'Idle 1', 'Wait2': 'Idle 2', 'Walk': 'Walk', 'Dash': 'Dash',
  'Run': 'Run', 'Jump': 'Jump', 'Fall': 'Fall',
  'Guard': 'Shield', 'EscapeF': 'Roll Forward', 'EscapeB': 'Roll Back',
  'Appeal': 'Taunt', 'Win1': 'Victory Pose 1', 'Win2': 'Victory Pose 2',
}

const ANIM_CATEGORIES = {
  'Grounded Attacks': ['Attack11', 'Attack12', 'Attack13', 'AttackDash', 'AttackHi3', 'AttackLw3', 'AttackS3', 'AttackHi4', 'AttackLw4', 'AttackS4'],
  'Aerials': ['AttackAirN', 'AttackAirHi', 'AttackAirF', 'AttackAirLw', 'AttackAirB'],
  'Specials': ['SpecialN', 'SpecialHi', 'SpecialLw', 'SpecialS'],
  'Grabs & Throws': ['Catch', 'Throw'],
  'Movement': ['Wait', 'Walk', 'Dash', 'Run', 'Jump', 'Fall'],
  'Defense': ['Guard', 'Escape'],
  'Misc': ['Appeal', 'Win'],
}

const extractAnimName = (symbol) => {
  const match = symbol.match(/_ACTION_(.+?)_figatree$/)
  if (match) return match[1]
  const match2 = symbol.match(/_ACTION_(.+)$/)
  if (match2) return match2[1]
  return symbol
}

const getAnimDisplayName = (symbol) => {
  const coreName = extractAnimName(symbol)
  return ANIM_NAMES[coreName] || coreName
}

const getAnimCategory = (symbol) => {
  const coreName = extractAnimName(symbol)
  for (const [category, prefixes] of Object.entries(ANIM_CATEGORIES)) {
    if (prefixes.some(prefix => coreName.startsWith(prefix))) {
      return category
    }
  }
  return 'Other'
}

const groupAnimations = (animList) => {
  const grouped = {}
  for (const symbol of animList) {
    const category = getAnimCategory(symbol)
    if (!grouped[category]) grouped[category] = []
    grouped[category].push(symbol)
  }
  const categoryOrder = Object.keys(ANIM_CATEGORIES).concat(['Other'])
  const sorted = {}
  for (const cat of categoryOrder) {
    if (grouped[cat]?.length > 0) sorted[cat] = grouped[cat]
  }
  return sorted
}

const API_URL = 'http://127.0.0.1:5000'

let viewerStarting = false

const EmbeddedModelViewer = ({ character, skinId, datFile, sceneFile, ajFile, logsPath, onClose }) => {
  const placeholderRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // Camera state
  const [isDragging, setIsDragging] = useState(false)
  const [dragButton, setDragButton] = useState(null)
  const lastMousePos = useRef({ x: 0, y: 0 })

  // Animation state
  const [animPlaying, setAnimPlaying] = useState(false)
  const [animFrame, setAnimFrame] = useState(0)
  const [animFrameCount, setAnimFrameCount] = useState(0)
  const [animList, setAnimList] = useState([])
  const [selectedAnim, setSelectedAnim] = useState('')
  const [animFilter, setAnimFilter] = useState('')

  // Check if Electron API is available
  const hasElectron = typeof window !== 'undefined' && window.electron?.viewerStart

  console.log('[EmbeddedViewer] Component rendered, hasElectron:', hasElectron, 'character:', character, 'skinId:', skinId)

  // Start the embedded viewer
  const startViewer = useCallback(async () => {
    console.log('[EmbeddedViewer] startViewer called, viewerStarting:', viewerStarting)
    if (viewerStarting) {
      console.log('[EmbeddedViewer] Already starting, skipping')
      return
    }
    viewerStarting = true

    try {
      setIsLoading(true)
      setError(null)

      if (!hasElectron) {
        console.error('[EmbeddedViewer] No Electron API available!')
        throw new Error('Embedded viewer requires Electron environment')
      }

      // If character and skinId are provided, fetch paths from API
      let viewerPaths = { datFile, sceneFile, ajFile, logsPath }

      if (character && skinId && !datFile) {
        console.log('[EmbeddedViewer] Fetching paths for:', character, skinId)
        const response = await fetch(`${API_URL}/api/viewer/paths`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ character, skinId })
        })

        const data = await response.json()
        if (!data.success) {
          throw new Error(data.error || 'Failed to get viewer paths')
        }

        viewerPaths = {
          datFile: data.datFile,
          sceneFile: data.sceneFile,
          ajFile: data.ajFile,
          logsPath: data.logsPath
        }
        console.log('[EmbeddedViewer] Got paths:', viewerPaths)
      }

      console.log('[EmbeddedViewer] Starting viewer...')
      const result = await window.electron.viewerStart(viewerPaths)

      console.log('[EmbeddedViewer] Viewer started:', result)
      setIsConnected(result.connected)
      setIsLoading(false)

      // Request animation list
      window.electron.viewerGetAnimList()

    } catch (err) {
      console.error('[EmbeddedViewer] Failed to start:', err)
      setError(err.message || 'Failed to start viewer')
      setIsLoading(false)
    } finally {
      viewerStarting = false
    }
  }, [datFile, sceneFile, ajFile, logsPath, character, skinId, hasElectron])

  // Stop the viewer
  const stopViewer = useCallback(async () => {
    if (hasElectron) {
      await window.electron.viewerStop()
    }
    setIsConnected(false)
  }, [hasElectron])

  // Update viewer window position to match placeholder
  const updateViewerPosition = useCallback(() => {
    if (!placeholderRef.current || !hasElectron) return

    const rect = placeholderRef.current.getBoundingClientRect()
    // Account for device pixel ratio on high-DPI displays for size
    const dpr = window.devicePixelRatio || 1

    // Position: screenX/Y + rect offset (CSS pixels work for position)
    const x = Math.round(window.screenX + rect.left)
    const y = Math.round(window.screenY + rect.top)
    // Size: need to account for DPR
    const width = Math.round(rect.width * dpr)
    const height = Math.round(rect.height * dpr)

    console.log('[EmbeddedViewer] Updating position:', { x, y, width, height, dpr, rect: { w: rect.width, h: rect.height } })
    window.electron.viewerResize(x, y, width, height)
  }, [hasElectron])

  // Handle messages from viewer
  useEffect(() => {
    if (!hasElectron) return

    const handleMessage = (message) => {
      console.log('[EmbeddedViewer] Message:', message.type)

      switch (message.type) {
        case 'ready':
          setIsConnected(true)
          setIsLoading(false)
          // Position the viewer window after a brief delay to ensure DOM is ready
          setTimeout(() => updateViewerPosition(), 100)
          break
        case 'animList':
          setAnimList(message.symbols || [])
          break
        case 'animLoaded':
          setSelectedAnim(message.symbol)
          setAnimFrameCount(message.frameCount || 0)
          setAnimFrame(0)
          setAnimPlaying(true)
          break
      }
    }

    const cleanup = window.electron.onViewerMessage(handleMessage)
    return cleanup
  }, [hasElectron, updateViewerPosition])

  // Keep viewer positioned when window moves/resizes
  useEffect(() => {
    if (!isConnected || !hasElectron) return

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
  }, [isConnected, hasElectron, updateViewerPosition])

  // Start viewer on mount
  useEffect(() => {
    startViewer()
    return () => {
      stopViewer()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Mouse handlers for camera control
  const handleMouseDown = (e) => {
    if (e.button === 0 || e.button === 2) {
      setIsDragging(true)
      setDragButton(e.button)
      lastMousePos.current = { x: e.clientX, y: e.clientY }
      e.preventDefault()
    }
  }

  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !hasElectron) return

    const dx = e.clientX - lastMousePos.current.x
    const dy = e.clientY - lastMousePos.current.y
    lastMousePos.current = { x: e.clientX, y: e.clientY }

    if (dragButton === 0) {
      // Left drag: rotate
      window.electron.viewerCamera(dy * 0.5, dx * 0.5, 0, 0, 0)
    } else if (dragButton === 2) {
      // Right drag: pan
      window.electron.viewerCamera(0, 0, 0, dx * 0.01, -dy * 0.01)
    }
  }, [isDragging, dragButton, hasElectron])

  const handleMouseUp = () => {
    setIsDragging(false)
    setDragButton(null)
  }

  const handleWheel = useCallback((e) => {
    if (!hasElectron) return
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.05 : 0.05
    window.electron.viewerCamera(0, 0, delta, 0, 0)
  }, [hasElectron])

  // Animation controls
  const toggleAnimation = () => {
    if (hasElectron) {
      window.electron.viewerAnimToggle()
      setAnimPlaying(!animPlaying)
    }
  }

  const setFrame = (frame) => {
    if (hasElectron) {
      window.electron.viewerAnimSetFrame(frame)
      setAnimFrame(frame)
    }
  }

  const loadAnimation = (symbol) => {
    if (hasElectron) {
      window.electron.viewerLoadAnim(symbol)
    }
  }

  // Prevent context menu on right-click
  const handleContextMenu = (e) => e.preventDefault()

  // Group and filter animations
  const groupedAnims = groupAnimations(animList)
  const filteredGroups = {}
  for (const [cat, anims] of Object.entries(groupedAnims)) {
    const filtered = anims.filter(a =>
      getAnimDisplayName(a).toLowerCase().includes(animFilter.toLowerCase()) ||
      a.toLowerCase().includes(animFilter.toLowerCase())
    )
    if (filtered.length > 0) filteredGroups[cat] = filtered
  }

  // Render fallback for non-Electron
  if (!hasElectron) {
    return (
      <div className="model-viewer-overlay" onClick={onClose}>
        <div className="model-viewer-container" onClick={(e) => e.stopPropagation()}>
          <div className="model-viewer-header">
            <h3>3D Viewer</h3>
            <button className="model-viewer-close" onClick={onClose}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div className="model-viewer-content">
            <div className="model-viewer-status">
              <p>Embedded viewer requires Electron environment.</p>
              <p>Please use the streaming viewer in browser mode.</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="model-viewer-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="model-viewer-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="model-viewer-header">
          <h3>3D Viewer - {character}</h3>
          <button className="model-viewer-close" onClick={onClose}>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Main content */}
        <div className="model-viewer-content">
          {/* Viewer placeholder - this is where the embedded window appears */}
          <div
            ref={placeholderRef}
            className="model-viewer-canvas-container"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            onContextMenu={handleContextMenu}
          >
            {isLoading && (
              <div className="model-viewer-status">
                <div className="model-viewer-spinner" />
                <p>Loading viewer...</p>
              </div>
            )}
            {error && (
              <div className="model-viewer-status">
                <p className="model-viewer-error">{error}</p>
                <button className="btn-save" onClick={startViewer}>Retry</button>
              </div>
            )}
            {!isLoading && !error && !isConnected && (
              <div className="model-viewer-status">
                <div className="model-viewer-spinner" />
                <p>Connecting to viewer...</p>
              </div>
            )}
            {isConnected && (
              <div className="model-viewer-hint">
                Viewer window active - drag to rotate, scroll to zoom
              </div>
            )}
          </div>

          {/* Animation sidebar */}
          {isConnected && animList.length > 0 && (
            <div className="model-viewer-sidebar">
              <h4>Animations</h4>
              <input
                type="text"
                placeholder="Search animations..."
                value={animFilter}
                onChange={(e) => setAnimFilter(e.target.value)}
                className="model-viewer-search"
              />

              <div className="model-viewer-anim-list">
                {Object.entries(filteredGroups).map(([category, anims]) => (
                  <div key={category} className="model-viewer-anim-category">
                    <div className="model-viewer-category-header">{category}</div>
                    {anims.map(anim => (
                      <div
                        key={anim}
                        onClick={() => loadAnimation(anim)}
                        className={`model-viewer-anim-item ${selectedAnim === anim ? 'selected' : ''}`}
                      >
                        {getAnimDisplayName(anim)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Animation controls footer */}
        {isConnected && animFrameCount > 0 && (
          <div className="model-viewer-controls">
            <button onClick={toggleAnimation} className="model-viewer-play-btn">
              {animPlaying ? '⏸' : '▶'}
            </button>
            <input
              type="range"
              min={0}
              max={animFrameCount - 1}
              value={animFrame}
              onChange={(e) => setFrame(parseFloat(e.target.value))}
              className="model-viewer-slider"
            />
            <span className="model-viewer-frame-label">
              {Math.floor(animFrame)} / {Math.floor(animFrameCount)}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default EmbeddedModelViewer
