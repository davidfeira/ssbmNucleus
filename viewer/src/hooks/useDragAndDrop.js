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
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [reordering, setReordering] = useState(false)
  const [previewOrder, setPreviewOrder] = useState(null) // Live preview of reordered items during drag
  const [dragTargetFolder, setDragTargetFolder] = useState(null) // Folder being hovered over during drag
  const justDraggedRef = useRef(false) // Prevent click from firing right after drag

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
    if (dragOverIndex !== index) {
      setDragOverIndex(index)

      // Calculate new preview order
      const currentOrder = previewOrder || [...items]

      // Find current position of dragged item in preview
      const draggedCurrentPos = currentOrder.findIndex(item => item.id === draggedItem.id)
      if (draggedCurrentPos === -1) return

      // Skip if already at target position in preview
      if (draggedCurrentPos === index) return

      // Create new order with item moved to target position
      const newOrder = [...currentOrder]
      const [removed] = newOrder.splice(draggedCurrentPos, 1)
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

  const handleSkinDrop = async (e, toIndex) => {
    e.preventDefault()
    if (!draggedItem) return

    const fromIndex = dragStartIndex

    if (fromIndex === toIndex || !selectedCharacter) {
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
        // Refresh metadata to get updated order
        await onRefresh()
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    } finally {
      setReordering(false)
      setDraggedItem(null)
      setDragStartIndex(null)
      setDragOverIndex(null)
      setPreviewOrder(null)
    }
  }

  const handleVariantDrop = async (e, toIndex) => {
    e.preventDefault()
    if (!draggedItem) return

    const fromIndex = dragStartIndex

    if (fromIndex === toIndex || !selectedStage) {
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
        // Refresh stage variants and metadata
        await fetchStageVariants()
        await onRefresh()
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    } finally {
      setReordering(false)
      setDraggedItem(null)
      setDragStartIndex(null)
      setDragOverIndex(null)
      setPreviewOrder(null)
    }
  }

  const handleDragEnd = () => {
    setDraggedItem(null)
    setDragStartIndex(null)
    setDragOverIndex(null)
    setPreviewOrder(null)
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
