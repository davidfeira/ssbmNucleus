import { useState, useRef } from 'react'
import { useAutoAnimate } from '@formkit/auto-animate/react'
import { buildDisplayList, countSkinsInFolder } from '../../utils/storageViewerUtils'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL } from '../../config'
import FolderCard from './FolderCard'

const SkeletonCard = () => (
  <div className="stage-card skeleton-card">
    <div className="stage-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '60%', height: '12px' }}></div>
  </div>
)

export default function CustomStagesGrid({
  customStages,
  isLoading,
  onSelectStage,
  onBack,
  onImportZip,
  onScanIso,
  importing,
  onRefresh
}) {
  // Drag state
  const [draggedItem, setDraggedItem] = useState(null) // { id }
  const [dragStartIndex, setDragStartIndex] = useState(null)
  const [previewOrder, setPreviewOrder] = useState(null)
  const [reordering, setReordering] = useState(false)
  const [justDroppedId, setJustDroppedId] = useState(null)
  const dragOverIndexRef = useRef(null)
  const dropInProgressRef = useRef(false)
  const justDraggedRef = useRef(false)

  // Folder state
  const [expandedFolders, setExpandedFolders] = useState({})
  const [editingFolderId, setEditingFolderId] = useState(null)
  const [editingFolderName, setEditingFolderName] = useState('')

  const isDraggingActive = draggedItem !== null
  const itemsForDisplay = previewOrder || customStages
  const displayList = buildDisplayList(itemsForDisplay, expandedFolders)

  const [animateRef, enableAnimations] = useAutoAnimate({ duration: 150 })
  enableAnimations(!isDraggingActive)

  // ── Drag handlers ──────────────────────────────────────────
  const handleDragStart = (e, index, items) => {
    setDraggedItem({ id: items[index].id })
    setDragStartIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDragEnter = (e, index, items) => {
    e.preventDefault()
    if (!draggedItem) return
    if (dragOverIndexRef.current === index) return
    dragOverIndexRef.current = index

    const currentPos = items.findIndex(item => item.id === draggedItem.id)
    if (currentPos === -1 || currentPos === index) return

    const newOrder = [...items]
    const [removed] = newOrder.splice(currentPos, 1)
    newOrder.splice(index, 0, removed)
    setPreviewOrder(newOrder)
  }

  const cleanupDrag = () => {
    dragOverIndexRef.current = null
    dropInProgressRef.current = false
    setReordering(false)
    setDraggedItem(null)
    setDragStartIndex(null)
    setPreviewOrder(null)
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    if (!draggedItem || dragOverIndexRef.current === null) return
    dropInProgressRef.current = true

    const fromIndex = dragStartIndex
    const toIndex = dragOverIndexRef.current

    if (fromIndex === toIndex || fromIndex === null) {
      cleanupDrag()
      return
    }

    setReordering(true)
    try {
      const response = await fetch(`${API_URL}/custom-stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fromIndex, toIndex })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        const droppedId = draggedItem.id
        setJustDroppedId(droppedId)
        setTimeout(() => setJustDroppedId(null), 400)
        await onRefresh()
        requestAnimationFrame(cleanupDrag)
        return
      }
      alert(`Reorder failed: ${data.error}`)
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    }
    cleanupDrag()
  }

  const handleDragEnd = () => {
    if (!dropInProgressRef.current) cleanupDrag()
    justDraggedRef.current = true
    setTimeout(() => { justDraggedRef.current = false }, 100)
  }

  // ── Folder handlers ────────────────────────────────────────
  const toggleFolder = async (folderId) => {
    setExpandedFolders(prev => ({ ...prev, [folderId]: !(prev[folderId] ?? true) }))
    try {
      await fetch(`${API_URL}/custom-stages/folders/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderId })
      })
    } catch (err) {
      console.error('Toggle folder error:', err)
    }
  }

  const handleCreateFolder = async () => {
    try {
      const response = await fetch(`${API_URL}/custom-stages/folders/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Folder' })
      })
      const data = await response.json()
      if (data.success) {
        await onRefresh()
        setEditingFolderId(data.folder.id)
        setEditingFolderName(data.folder.name)
      } else {
        alert(`Create folder failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Create folder error: ${err.message}`)
    }
  }

  const saveFolderName = async (folderId) => {
    if (!editingFolderName.trim()) {
      setEditingFolderId(null)
      return
    }
    try {
      const response = await fetch(`${API_URL}/custom-stages/folders/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderId, newName: editingFolderName.trim() })
      })
      const data = await response.json()
      if (data.success) {
        await onRefresh()
      } else {
        alert(`Rename folder failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Rename folder error: ${err.message}`)
    } finally {
      setEditingFolderId(null)
      setEditingFolderName('')
    }
  }

  const deleteFolder = async (folderId) => {
    if (!confirm('Delete this folder? Stages inside will move out, not be deleted.')) return
    try {
      const response = await fetch(`${API_URL}/custom-stages/folders/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderId })
      })
      const data = await response.json()
      if (data.success) {
        await onRefresh()
      } else {
        alert(`Delete folder failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Delete folder error: ${err.message}`)
    }
  }

  // ── Render ─────────────────────────────────────────────────
  const stageCount = customStages.filter(s => s.type !== 'folder').length

  return (
    <div className="grid-wrapper">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className="mode-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('back'); onBack(); }}
        >
          ← Back to Stages
        </button>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <button
            className="character-action-button"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); handleCreateFolder(); }}
          >
            New Folder
          </button>
        </div>
      </div>

      <div className={`custom-stages-grid${isDraggingActive ? ' is-dragging' : ''}`} ref={animateRef}>
        {isLoading ? (
          Array.from({ length: 8 }).map((_, idx) => (
            <SkeletonCard key={`skeleton-cs-${idx}`} />
          ))
        ) : stageCount === 0 && customStages.length === 0 ? (
          <div className="no-skins-message" style={{ gridColumn: '1 / -1' }}>
            <p>No custom stages yet. Import a stage package or scan an ISO.</p>
          </div>
        ) : displayList.map((entry, idx) => {
          if (entry.type === 'folder') {
            const folderId = entry.folder.id
            return (
              <FolderCard
                key={folderId}
                folder={entry.folder}
                isExpanded={entry.isExpanded}
                displayIdx={idx}
                arrayIdx={entry.arrayIndex}
                isDragging={draggedItem && draggedItem.id === folderId}
                isDropTarget={false}
                isJustDropped={justDroppedId === folderId}
                isEditing={editingFolderId === folderId}
                editingFolderName={editingFolderName}
                folderSkinCount={countSkinsInFolder(folderId, customStages)}
                reordering={reordering}
                onToggle={toggleFolder}
                onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                onDragOver={handleDragOver}
                onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === folderId), itemsForDisplay)}
                onDragLeave={() => {}}
                onDrop={handleDrop}
                onDragEnd={handleDragEnd}
                onEditingFolderNameChange={setEditingFolderName}
                onSaveFolderName={saveFolderName}
                onCancelEdit={() => setEditingFolderId(null)}
                onStartEditing={(folder) => {
                  setEditingFolderId(folder.id)
                  setEditingFolderName(folder.name)
                }}
                onDelete={deleteFolder}
                justDraggedRef={justDraggedRef}
              />
            )
          }

          const stage = entry.skin
          const stageId = stage.id
          const isDragging = draggedItem && draggedItem.id === stageId
          const isJustDropped = justDroppedId === stageId
          const classes = [
            'stage-card',
            isDragging && 'dragging',
            isJustDropped && 'just-dropped'
          ].filter(Boolean).join(' ')

          return (
            <div
              key={stageId}
              className={classes}
              draggable={!reordering}
              onMouseEnter={playHoverSound}
              onDragStart={(e) => handleDragStart(e, itemsForDisplay.findIndex(s => s.id === stageId), itemsForDisplay)}
              onDragOver={handleDragOver}
              onDragEnter={(e) => handleDragEnter(e, itemsForDisplay.findIndex(s => s.id === stageId), itemsForDisplay)}
              onDrop={handleDrop}
              onDragEnd={handleDragEnd}
              onClick={() => {
                if (justDraggedRef.current) return
                playSound('boop')
                onSelectStage(stage)
              }}
            >
              <div className="stage-icon-container">
                {stage.has_icon ? (
                  <img
                    src={stage.icon_url}
                    alt={stage.name}
                    className="stage-icon"
                    style={{ imageRendering: 'pixelated' }}
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextSibling.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div className="stage-placeholder" style={{ display: stage.has_icon ? 'none' : 'flex' }}>
                  {stage.name[0]}
                </div>
              </div>
              <div className="stage-info">
                <h3 className="stage-name">{stage.name}</h3>
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
        <label
          className="intake-import-btn"
          style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start'); }}
        >
          {importing ? 'Importing...' : 'Import ZIP'}
          <input
            type="file"
            accept=".zip"
            onChange={onImportZip}
            disabled={importing}
            style={{ display: 'none' }}
          />
        </label>
        <label
          className="intake-import-btn"
          style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start'); }}
        >
          {importing ? 'Scanning...' : 'Scan ISO'}
          <input
            type="file"
            accept=".iso,.gcm"
            onChange={onScanIso}
            disabled={importing}
            style={{ display: 'none' }}
          />
        </label>
      </div>
    </div>
  )
}
