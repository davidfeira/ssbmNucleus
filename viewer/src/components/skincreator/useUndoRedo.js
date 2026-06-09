import { useState, useEffect } from 'react'

// Undo/redo stack for the paint canvas, including keyboard shortcuts and
// clearing the stacks when switching textures.
export function useUndoRedo({ paintCanvasRef, sendTextureUpdate, selectedTextureIndex, isOpen, skinCreatorStep }) {
  const [undoStack, setUndoStack] = useState([])
  const [redoStack, setRedoStack] = useState([])
  const maxUndoSteps = 50

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

  return { undoStack, redoStack, saveToUndoStack, undo, redo }
}
