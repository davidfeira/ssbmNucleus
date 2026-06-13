import { useRef, useState } from 'react'
import { API_URL } from '../../config'
import { playSound, playHoverSound } from '../../utils/sounds'

const SkeletonCard = () => (
  <div className="character-card skeleton-card">
    <div className="character-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '60%', height: '12px' }}></div>
  </div>
)

export default function CustomCharactersGrid({
  customCharacters,
  isLoading,
  onSelectCharacter,
  onBack,
  onRefresh
}) {
  // Drag-to-reorder state. previewOrder holds the live reordered list while a
  // drag is in flight; once dropped we persist to the backend and refresh.
  const [previewOrder, setPreviewOrder] = useState(null)
  const [reordering, setReordering] = useState(false)
  const draggedSlugRef = useRef(null)
  const justDraggedRef = useRef(false) // suppress the click that follows a drag

  const items = previewOrder || customCharacters

  const handleDragStart = (e, slug) => {
    draggedSlugRef.current = slug
    setPreviewOrder([...customCharacters])
    e.dataTransfer.effectAllowed = 'move'
    // Marking the payload as text/plain is what keeps the global import
    // overlay hidden: ImportFab only reacts to drags carrying 'Files'.
    e.dataTransfer.setData('text/plain', slug)
  }

  const handleDragEnter = (overIndex) => {
    const draggedSlug = draggedSlugRef.current
    if (!draggedSlug) return
    setPreviewOrder((prev) => {
      const list = prev ? [...prev] : [...customCharacters]
      const from = list.findIndex((c) => c.slug === draggedSlug)
      if (from === -1 || from === overIndex) return prev
      const [moved] = list.splice(from, 1)
      list.splice(overIndex, 0, moved)
      return list
    })
  }

  const handleDragEnd = async () => {
    justDraggedRef.current = true
    setTimeout(() => { justDraggedRef.current = false }, 100)

    const draggedSlug = draggedSlugRef.current
    const preview = previewOrder
    draggedSlugRef.current = null

    if (!draggedSlug || !preview) {
      setPreviewOrder(null)
      return
    }

    const fromIndex = customCharacters.findIndex((c) => c.slug === draggedSlug)
    const toIndex = preview.findIndex((c) => c.slug === draggedSlug)
    if (fromIndex === -1 || toIndex === -1 || fromIndex === toIndex) {
      setPreviewOrder(null)
      return
    }

    setReordering(true)
    try {
      const res = await fetch(`${API_URL}/custom-characters/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fromIndex, toIndex })
      })
      const data = await res.json()
      if (data.success) {
        playSound('boop')
        await onRefresh?.()
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    } finally {
      setReordering(false)
      setPreviewOrder(null)
    }
  }

  return (
    <div className="grid-wrapper">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className="mode-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('back'); onBack(); }}
        >
          ← Back to Characters
        </button>
      </div>

      <div
        className="characters-grid custom-characters-grid"
        onDragOver={(e) => { if (draggedSlugRef.current) e.preventDefault() }}
      >
        {isLoading ? (
          Array.from({ length: 8 }).map((_, idx) => (
            <SkeletonCard key={`skeleton-cc-${idx}`} />
          ))
        ) : items.length === 0 ? (
          <div className="no-skins-message" style={{ width: '100%' }}>
            <p>No custom characters yet. Import a fighter package or scan an ISO.</p>
          </div>
        ) : items.map((char, index) => (
          <div
            key={char.slug}
            className={`character-card${draggedSlugRef.current === char.slug ? ' dragging' : ''}`}
            draggable={!reordering}
            onDragStart={(e) => handleDragStart(e, char.slug)}
            onDragEnter={(e) => { e.preventDefault(); handleDragEnter(index) }}
            onDragOver={(e) => e.preventDefault()}
            onDragEnd={handleDragEnd}
            onMouseEnter={playHoverSound}
            onClick={() => {
              if (justDraggedRef.current) return
              playSound('boop')
              onSelectCharacter(char)
            }}
          >
            <div className="character-icon-container">
              {char.has_css_icon ? (
                <img
                  src={char.icon_url}
                  alt={char.name}
                  className="character-css-icon"
                  draggable={false}
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
              ) : null}
              <div className="character-placeholder" style={{ display: char.has_css_icon ? 'none' : 'flex' }}>
                <span className="character-initial">{char.name[0]}</span>
              </div>
            </div>
            <p className="skin-count">
              <span>{char.costume_count}</span> costume{char.costume_count !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
