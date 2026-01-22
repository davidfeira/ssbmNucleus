/**
 * useDragAndDrop Hook
 *
 * Manages drag-and-drop functionality for reordering skins and stage variants.
 * Handles drag state, visual preview, and API mutations for reordering.
 */

import { useState, useRef } from 'react'

export function useDragAndDrop({
  mode, // 'characters' or 'stages'
  selectedCharacter,
  selectedStage,
  API_URL,
  onRefresh,
  fetchStageVariants
}) {
  // State
  const [draggedItem, setDraggedItem] = useState(null) // { index, id }
  const [dragStartIndex, setDragStartIndex] = useState(null) // Original position when drag started
  const [dragOverIndex, setDragOverIndex] = useState(null) // For UI reactivity
  const [reordering, setReordering] = useState(false)
  const [previewOrder, setPreviewOrder] = useState(null) // Live preview of reordered items during drag
  const [dragTargetFolder, setDragTargetFolder] = useState(null) // Folder being hovered over during drag
  const [justDroppedId, setJustDroppedId] = useState(null) // ID of item that just dropped (for settle animation)
  const justDraggedRef = useRef(false) // Prevent click from firing right after drag
  const dropInProgressRef = useRef(false) // Track if drop is being processed
  const dragOverIndexRef = useRef(null) // Ref version for reliable access in handlers

  // Derived state
  const isDraggingActive = draggedItem !== null

  // Handlers
  const handleDragStart = (e, index, items) => {
    setDraggedItem({ index, id: items[index].id })
    setDragStartIndex(index) // Track original position for returning to same spot
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDragEnter = (e, index, items) => {
    e.preventDefault()
    if (!draggedItem) return

    // Only update if we've moved to a different position
    if (dragOverIndexRef.current !== index) {
      dragOverIndexRef.current = index // Update ref immediately
      setDragOverIndex(index) // Update state for UI

      // Find where the dragged item currently is in the items array
      const currentPos = items.findIndex(item => item.id === draggedItem.id)
      if (currentPos === -1 || currentPos === index) return

      // Move item from current position to target position
      const newOrder = [...items]
      const [removed] = newOrder.splice(currentPos, 1)
      newOrder.splice(index, 0, removed)

      setPreviewOrder(newOrder)
    }
  }

  const handleDragLeave = (e) => {
    // Only clear if leaving the container entirely
    if (e.currentTarget === e.target) {
      setDragOverIndex(null)
    }
  }

  const handleSkinDrop = async (e) => {
    e.preventDefault()
    if (!draggedItem || dragOverIndexRef.current === null) return

    dropInProgressRef.current = true

    const fromIndex = dragStartIndex
    const toIndex = dragOverIndexRef.current

    if (fromIndex === toIndex || fromIndex === null || !selectedCharacter) {
      dropInProgressRef.current = false
      dragOverIndexRef.current = null
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
        // Trigger settle animation on dropped item
        const droppedId = draggedItem.id
        setJustDroppedId(droppedId)
        setTimeout(() => setJustDroppedId(null), 400) // Clear after animation

        // Refresh metadata to get updated order
        await onRefresh()

        // Clear drag state after refresh completes - slight delay to let React render new data first
        requestAnimationFrame(() => {
          dropInProgressRef.current = false
          dragOverIndexRef.current = null
          setReordering(false)
          setDraggedItem(null)
          setDragStartIndex(null)
          setDragOverIndex(null)
          setPreviewOrder(null)
        })
        return
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    }
    // Only clear on error/cancel - success case handles cleanup above
    dropInProgressRef.current = false
    dragOverIndexRef.current = null
    setReordering(false)
    setDraggedItem(null)
    setDragStartIndex(null)
    setDragOverIndex(null)
    setPreviewOrder(null)
  }

  const handleVariantDrop = async (e) => {
    e.preventDefault()
    if (!draggedItem || dragOverIndexRef.current === null) return

    dropInProgressRef.current = true // Mark drop as in progress before dragEnd fires

    const fromIndex = dragStartIndex
    const toIndex = dragOverIndexRef.current // Use ref for reliable value

    if (fromIndex === toIndex || fromIndex === null || !selectedStage) {
      dropInProgressRef.current = false
      dragOverIndexRef.current = null
      setDraggedItem(null)
      setDragStartIndex(null)
      setDragOverIndex(null)
      setPreviewOrder(null)
      return
    }

    setReordering(true)

    try {
      const response = await fetch(`${API_URL}/storage/stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageFolder: selectedStage.folder,
          fromIndex,
          toIndex
        })
      })

      const data = await response.json()

      if (data.success) {
        // Trigger settle animation on dropped item
        const droppedId = draggedItem.id
        setJustDroppedId(droppedId)
        setTimeout(() => setJustDroppedId(null), 400) // Clear after animation

        // Refresh stage variants and metadata
        await fetchStageVariants()
        await onRefresh()

        // Clear drag state after refresh completes - slight delay to let React render new data first
        requestAnimationFrame(() => {
          dropInProgressRef.current = false
          dragOverIndexRef.current = null
          setReordering(false)
          setDraggedItem(null)
          setDragStartIndex(null)
          setDragOverIndex(null)
          setPreviewOrder(null)
        })
        return
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    }
    // Only clear on error/cancel - success case handles cleanup above
    dropInProgressRef.current = false
    dragOverIndexRef.current = null
    setReordering(false)
    setDraggedItem(null)
    setDragStartIndex(null)
    setDragOverIndex(null)
    setPreviewOrder(null)
  }

  const handleDragEnd = () => {
    // If drop is in progress, let the drop handler clean up
    // This prevents the flash when previewOrder is cleared before refresh completes
    if (!dropInProgressRef.current) {
      dragOverIndexRef.current = null
      setDraggedItem(null)
      setDragStartIndex(null)
      setDragOverIndex(null)
      setPreviewOrder(null)
    }
    setDragTargetFolder(null)
    // Prevent click from firing right after drag
    justDraggedRef.current = true
    setTimeout(() => { justDraggedRef.current = false }, 100)
  }

  return {
    // State
    draggedItem,
    dragStartIndex,
    dragOverIndex,
    previewOrder,
    reordering,
    dragTargetFolder,
    justDraggedRef,
    isDraggingActive,
    justDroppedId,
    setJustDroppedId, // Expose setter for custom drop handlers
    setDragTargetFolder, // Expose setter for folder drag logic

    // Handlers
    handleDragStart,
    handleDragOver,
    handleDragEnter,
    handleDragLeave,
    handleSkinDrop,
    handleVariantDrop,
    handleDragEnd
  }
}
