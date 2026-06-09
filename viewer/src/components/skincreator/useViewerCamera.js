import { useState, useRef } from 'react'

// Mouse/wheel camera controls for the embedded 3D viewer (Electron IPC).
export function useViewerCamera({ hasElectron, viewerWs }) {
  const [viewerDragging, setViewerDragging] = useState(false)
  const [viewerDragButton, setViewerDragButton] = useState(null)
  const viewerLastMousePos = useRef({ x: 0, y: 0 })

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

  return {
    handleViewerMouseDown,
    handleViewerMouseMove,
    handleViewerMouseUp,
    handleViewerWheel,
    handleViewerContextMenu
  }
}
