import { useState, useRef } from 'react'
import { getCanvasCoords, drawBrush, eraseBrush, drawLine, floodFill } from './canvasUtils'

// Drawing tools state and paint canvas mouse handlers.
export function usePaintCanvas({ paintCanvasRef, saveToUndoStack, sendTextureUpdate }) {
  const [isDrawing, setIsDrawing] = useState(false)
  const isDrawingRef = useRef(false) // Ref for interval callback access
  const lastDrawPos = useRef(null)

  // Drawing tools state
  const [activeTool, setActiveTool] = useState('pencil') // pencil, eraser, fill, eyedropper
  const [drawColor, setDrawColor] = useState('#ff0000')
  const [brushSize, setBrushSize] = useState(1)

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

    const canvas = paintCanvasRef.current
    const coords = getCanvasCoords(canvas, e)
    if (!coords) return

    if (activeTool === 'eyedropper') {
      eyedropperPick(coords.x, coords.y)
      return
    }

    if (activeTool === 'fill') {
      saveToUndoStack()
      floodFill(canvas, coords.x, coords.y, drawColor)
      sendTextureUpdate()
      return
    }

    // Pencil or eraser - start drawing
    saveToUndoStack()
    setIsDrawing(true)
    isDrawingRef.current = true

    if (activeTool === 'pencil') {
      drawBrush(canvas, coords.x, coords.y, drawColor, brushSize)
    } else if (activeTool === 'eraser') {
      eraseBrush(canvas, coords.x, coords.y, brushSize)
    }
    lastDrawPos.current = coords
  }

  const handlePaintMouseMove = (e) => {
    if (!isDrawing) return
    const canvas = paintCanvasRef.current
    const coords = getCanvasCoords(canvas, e)
    if (!coords) return

    const toolFn = activeTool === 'eraser'
      ? (x, y) => eraseBrush(canvas, x, y, brushSize)
      : (x, y) => drawBrush(canvas, x, y, drawColor, brushSize)

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

  return {
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
  }
}
