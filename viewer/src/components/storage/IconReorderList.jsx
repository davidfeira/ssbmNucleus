import { useState } from 'react'
import { playSound } from '../../utils/sounds'

/**
 * IconReorderList - the icon list in the CSS/SSS layout editor right panel.
 *
 * Rows show a thumbnail + label, support click / shift-click selection,
 * right-click for the properties popup, and drag-and-drop reordering
 * (identity moves between slots; the editors re-zip the slot layout fields).
 */
export default function IconReorderList({
  icons,
  selectedIndices,
  onSelect,          // (indices: number[]) => void
  onContextMenu,     // (x, y) => void
  onReorder,         // (from, to) => void
  getLabel,          // (icon, idx) => string
  getIconUrl         // (icon) => string | null
}) {
  const [dragIdx, setDragIdx] = useState(null)
  const [overIdx, setOverIdx] = useState(null)

  const handleClick = (e, idx) => {
    playSound('boop')
    if (e.shiftKey) {
      const s = new Set(selectedIndices)
      if (s.has(idx)) s.delete(idx); else s.add(idx)
      onSelect([...s])
    } else {
      onSelect([idx])
    }
  }

  const handleContextMenu = (e, idx) => {
    e.preventDefault()
    if (!selectedIndices.includes(idx)) onSelect([idx])
    onContextMenu(e.clientX, e.clientY)
  }

  const endDrag = () => {
    setDragIdx(null)
    setOverIdx(null)
  }

  return (
    <div className="sss-icon-list">
      {icons.map((icon, idx) => {
        const iconUrl = getIconUrl ? getIconUrl(icon) : null
        const isDragTarget = dragIdx !== null && overIdx === idx && dragIdx !== idx
        const dropClass = isDragTarget ? (dragIdx < idx ? 'drop-after' : 'drop-before') : ''

        return (
          <div
            key={idx}
            className={`sss-icon-item ${selectedIndices.includes(idx) ? 'selected' : ''} ${dragIdx === idx ? 'dragging' : ''} ${dropClass}`}
            onClick={(e) => handleClick(e, idx)}
            onContextMenu={(e) => handleContextMenu(e, idx)}
            draggable
            onDragStart={(e) => {
              setDragIdx(idx)
              e.dataTransfer.effectAllowed = 'move'
              // Required for Firefox to start the drag
              e.dataTransfer.setData('text/plain', String(idx))
            }}
            onDragOver={(e) => {
              e.preventDefault()
              e.dataTransfer.dropEffect = 'move'
              if (overIdx !== idx) setOverIdx(idx)
            }}
            onDrop={(e) => {
              e.preventDefault()
              if (dragIdx !== null && dragIdx !== idx) {
                playSound('tick')
                onReorder(dragIdx, idx)
              }
              endDrag()
            }}
            onDragEnd={endDrag}
          >
            <span className="sss-icon-idx">{idx}</span>
            <span className="sss-icon-thumb">
              {iconUrl ? (
                <img src={iconUrl} alt="" draggable={false} onError={(e) => { e.target.style.display = 'none' }} />
              ) : (
                <span className="sss-icon-thumb-empty">?</span>
              )}
            </span>
            <span className="sss-icon-name">{getLabel(icon, idx)}</span>
          </div>
        )
      })}
    </div>
  )
}
