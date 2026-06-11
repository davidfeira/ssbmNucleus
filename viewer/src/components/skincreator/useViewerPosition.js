import { useEffect, useCallback, useRef } from 'react'

// Keeps the embedded viewer window positioned over the 3D preview container.
// Only sends a reposition when the target rect actually changed -- calling
// SetWindowPos unconditionally on a timer makes the native window jitter.
export function useViewerPosition({ skinCreatorCanvasRef, hasElectron, viewerWs, skinCreatorStep, panelSizes }) {
  const lastPosRef = useRef(null)

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

    const last = lastPosRef.current
    if (last && last.x === x && last.y === y && last.width === width && last.height === height) {
      return
    }
    lastPosRef.current = { x, y, width, height }
    window.electron.viewerResize(x, y, width, height)
  }, [hasElectron])

  // Keep viewer positioned when window moves/resizes
  useEffect(() => {
    if (!viewerWs || !hasElectron || skinCreatorStep !== 'edit') return

    const handleResize = () => updateViewerPosition()

    window.addEventListener('resize', handleResize)
    window.addEventListener('scroll', handleResize, true)

    // Track container layout changes directly
    const ro = new ResizeObserver(handleResize)
    if (skinCreatorCanvasRef.current) ro.observe(skinCreatorCanvasRef.current)

    // Also poll for window MOVES (no DOM event exists) -- cheap because
    // updateViewerPosition no-ops when nothing changed
    const intervalId = setInterval(updateViewerPosition, 500)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('scroll', handleResize, true)
      ro.disconnect()
      clearInterval(intervalId)
    }
  }, [viewerWs, hasElectron, skinCreatorStep, updateViewerPosition])

  // Update viewer position when panel sizes change
  useEffect(() => {
    if (viewerWs && hasElectron && skinCreatorStep === 'edit') {
      updateViewerPosition()
    }
  }, [panelSizes, viewerWs, hasElectron, skinCreatorStep, updateViewerPosition])

  return updateViewerPosition
}
