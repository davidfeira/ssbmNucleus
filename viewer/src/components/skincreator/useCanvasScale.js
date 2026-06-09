import { useState, useEffect, useRef, useCallback } from 'react'

// Canvas container sizing for dynamic scaling of the paint canvas.
export function useCanvasScale({ skinCreatorStep, selectedTextureIndex, modelTextures, paintCanvasRef }) {
  const canvasContainerRef = useRef(null)
  const [canvasContainerSize, setCanvasContainerSize] = useState({ width: 600, height: 600 })

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

  return { canvasContainerRef, updateCanvasScale }
}
