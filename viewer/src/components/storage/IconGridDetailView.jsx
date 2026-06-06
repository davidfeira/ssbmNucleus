/**
 * IconGridDetailView - Labeled-icon view for a CSS icon grid mod.
 *
 * Fetches the normalized mod payload from /menus/css/icon_grid/<mod_id>/icons.
 * Renders the screenshot, an editable title, and one tile per labeled
 * character (normal + selected variants).
 */
import { useEffect, useState, useRef } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'

export default function IconGridDetailView({ modId, onBack, onModUpdated }) {
  const [mod, setMod] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingName, setEditingName] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const [savingName, setSavingName] = useState(false)
  const [relabelChar, setRelabelChar] = useState(null)
  const [relabelDraft, setRelabelDraft] = useState('')
  const [addingIcon, setAddingIcon] = useState(false)
  const [addCharName, setAddCharName] = useState('')
  const [addFile, setAddFile] = useState(null)
  const [addPreview, setAddPreview] = useState(null)
  const replaceInputRef = useRef(null)
  const addFileRef = useRef(null)
  const [replaceTarget, setReplaceTarget] = useState(null)
  const [bustCache, setBustCache] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch(`${API_URL}/menus/css/icon_grid/${modId}/icons`)
      .then(r => r.json())
      .then(res => {
        if (cancelled) return
        if (res.success) {
          setMod(res.mod)
        } else {
          setError(res.error || 'Failed to load mod')
        }
      })
      .catch(err => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [modId])

  const startEditingName = () => {
    setNameDraft(mod?.name || '')
    setEditingName(true)
  }

  const cancelEditingName = () => {
    setEditingName(false)
    setNameDraft('')
  }

  const saveName = async () => {
    const trimmed = nameDraft.trim()
    if (!trimmed || trimmed === mod?.name) {
      cancelEditingName()
      return
    }
    setSavingName(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/update/${modId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed })
      })
      const result = await res.json()
      if (result.success) {
        setMod(result.mod)
        onModUpdated?.(result.mod)
        setEditingName(false)
      } else {
        alert(`Rename failed: ${result.error}`)
      }
    } catch (err) {
      alert(`Rename error: ${err.message}`)
    } finally {
      setSavingName(false)
    }
  }

  const startRelabel = (character) => {
    setRelabelChar(character)
    setRelabelDraft(character)
  }

  const cancelRelabel = () => {
    setRelabelChar(null)
    setRelabelDraft('')
  }

  const saveRelabel = async () => {
    const trimmed = relabelDraft.trim()
    if (!trimmed || trimmed === relabelChar) {
      cancelRelabel()
      return
    }
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/${modId}/relabel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_character: relabelChar, new_character: trimmed })
      })
      const result = await res.json()
      if (result.success) {
        setMod(result.mod)
        onModUpdated?.(result.mod)
        cancelRelabel()
      } else {
        alert(`Relabel failed: ${result.error}`)
      }
    } catch (err) {
      alert(`Relabel error: ${err.message}`)
    }
  }

  const handleReplaceClick = (character) => {
    setReplaceTarget(character)
    setTimeout(() => replaceInputRef.current?.click(), 0)
  }

  const handleReplaceFile = async (e) => {
    const file = e.target.files[0]
    if (!file || !replaceTarget) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    const form = new FormData()
    form.append('character', replaceTarget)
    form.append('file', file)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/${modId}/replace_icon`, {
        method: 'POST',
        body: form
      })
      const result = await res.json()
      if (result.success) {
        setMod(result.mod)
        onModUpdated?.(result.mod)
        setBustCache(c => c + 1)
      } else {
        alert(`Replace failed: ${result.error}`)
      }
    } catch (err) {
      alert(`Replace error: ${err.message}`)
    } finally {
      setReplaceTarget(null)
      if (replaceInputRef.current) replaceInputRef.current.value = ''
    }
  }

  const handleDeleteIcon = async (character) => {
    if (!confirm(`Delete icon for "${character}"?`)) return
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/${modId}/delete_icon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character })
      })
      const result = await res.json()
      if (result.success) {
        setMod(result.mod)
        onModUpdated?.(result.mod)
      } else {
        alert(`Delete failed: ${result.error}`)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    }
  }

  const handleAddFileSelect = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    setAddFile(file)
    const reader = new FileReader()
    reader.onload = (ev) => setAddPreview(ev.target.result)
    reader.readAsDataURL(file)
  }

  const handleAddSubmit = async () => {
    const name = addCharName.trim()
    if (!name || !addFile) return
    const form = new FormData()
    form.append('character', name)
    form.append('file', addFile)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/${modId}/add_icon`, {
        method: 'POST',
        body: form
      })
      const result = await res.json()
      if (result.success) {
        setMod(result.mod)
        onModUpdated?.(result.mod)
        setAddingIcon(false)
        setAddCharName('')
        setAddFile(null)
        setAddPreview(null)
      } else {
        alert(`Add failed: ${result.error}`)
      }
    } catch (err) {
      alert(`Add error: ${err.message}`)
    }
  }

  const cancelAdd = () => {
    setAddingIcon(false)
    setAddCharName('')
    setAddFile(null)
    setAddPreview(null)
  }

  const icons = mod?.icons || []

  return (
    <div className="icon-grid-detail" style={{ width: '100%' }}>
      {/* Hidden file input for replace */}
      <input
        ref={replaceInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleReplaceFile}
      />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <button
          className="mode-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onBack() }}
        >
          ← Back
        </button>
        {editingName ? (
          <input
            type="text"
            value={nameDraft}
            autoFocus
            disabled={savingName}
            onChange={(e) => setNameDraft(e.target.value)}
            onBlur={saveName}
            onKeyDown={(e) => {
              if (e.key === 'Enter') { e.preventDefault(); saveName() }
              else if (e.key === 'Escape') { e.preventDefault(); cancelEditingName() }
            }}
            style={{
              fontSize: '1.17em',
              fontWeight: 'bold',
              padding: '0.25rem 0.5rem',
              background: 'var(--color-bg-secondary, rgba(255,255,255,0.05))',
              border: '1px solid var(--color-border)',
              borderRadius: '4px',
              color: 'inherit',
              flex: '1 1 auto',
              minWidth: 0
            }}
          />
        ) : (
          <h3
            style={{ margin: 0, cursor: 'pointer' }}
            title="Click to rename"
            onClick={startEditingName}
          >
            {mod?.name || 'Icon Grid Mod'}
          </h3>
        )}
        {!editingName && (
          <button
            className="mode-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); startEditingName() }}
            title="Rename"
            style={{ padding: '0.25rem 0.6rem' }}
          >
            ✎
          </button>
        )}
      </div>

      {loading && (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
          Loading...
        </div>
      )}

      {error && (
        <div className="import-message error">{error}</div>
      )}

      {!loading && !error && mod && (
        <>
          {mod.screenshotUrl && (
            <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
              <img
                src={`${BACKEND_URL}${mod.screenshotUrl}`}
                alt={mod.name}
                style={{ width: '50%', borderRadius: '4px', display: 'block' }}
              />
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
              {icons.length} icon{icons.length === 1 ? '' : 's'}
            </span>
            <button
              className="mode-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setAddingIcon(true) }}
              style={{ padding: '0.3rem 0.75rem', fontSize: '0.85rem' }}
            >
              + Add Icon
            </button>
          </div>

          {addingIcon && (
            <div style={{
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              padding: '1rem',
              marginBottom: '1rem',
              background: 'var(--color-bg-secondary, rgba(255,255,255,0.03))'
            }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 150px' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    Character Name
                  </label>
                  <input
                    type="text"
                    value={addCharName}
                    autoFocus
                    placeholder="e.g. Goku"
                    onChange={(e) => setAddCharName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') cancelAdd()
                    }}
                    style={{
                      width: '100%',
                      padding: '0.35rem 0.5rem',
                      background: 'var(--color-bg-secondary, rgba(255,255,255,0.05))',
                      border: '1px solid var(--color-border)',
                      borderRadius: '4px',
                      color: 'inherit',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
                <div style={{ flex: '0 0 auto' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    Icon Image
                  </label>
                  <input
                    ref={addFileRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAddFileSelect}
                    style={{ fontSize: '0.85rem' }}
                  />
                </div>
                {addPreview && (
                  <div style={{
                    width: '64px', height: '56px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: '1px solid var(--color-border)', borderRadius: '4px',
                    background: 'rgba(0,0,0,0.2)'
                  }}>
                    <img src={addPreview} alt="preview" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', imageRendering: 'pixelated' }} />
                  </div>
                )}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="mode-btn"
                    disabled={!addCharName.trim() || !addFile}
                    onClick={handleAddSubmit}
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                  >
                    Add
                  </button>
                  <button
                    className="mode-btn"
                    onClick={cancelAdd}
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
              gap: '0.75rem'
            }}
          >
            {icons.map((c) => (
              <div
                key={c.character}
                className="icon-tile"
                style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  background: 'var(--color-bg-secondary, rgba(255,255,255,0.03))',
                  position: 'relative'
                }}
              >
                {/* Replace / Delete buttons */}
                <div style={{
                  position: 'absolute', top: '4px', right: '4px',
                  display: 'flex', gap: '2px', opacity: 0.6
                }}
                  className="icon-tile-actions"
                >
                  <button
                    onClick={() => handleReplaceClick(c.character)}
                    title="Replace icon image"
                    style={{
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '3px',
                      color: 'var(--color-text-muted)',
                      cursor: 'pointer',
                      fontSize: '0.7rem',
                      padding: '1px 4px',
                      lineHeight: '1.2'
                    }}
                  >
                    ↻
                  </button>
                  <button
                    onClick={() => handleDeleteIcon(c.character)}
                    title="Delete icon"
                    style={{
                      background: 'rgba(255,80,80,0.15)',
                      border: '1px solid rgba(255,80,80,0.3)',
                      borderRadius: '3px',
                      color: '#ff6666',
                      cursor: 'pointer',
                      fontSize: '0.7rem',
                      padding: '1px 4px',
                      lineHeight: '1.2'
                    }}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '80px' }}>
                  {c.iconUrl && (
                    <img
                      src={`${BACKEND_URL}${c.iconUrl}${bustCache ? `?v=${bustCache}` : ''}`}
                      alt={c.character}
                      style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', imageRendering: 'pixelated' }}
                    />
                  )}
                </div>
                <div style={{ textAlign: 'center', marginTop: '0.4rem', fontSize: '0.85rem' }}>
                  {relabelChar === c.character ? (
                    <input
                      type="text"
                      value={relabelDraft}
                      autoFocus
                      onChange={(e) => setRelabelDraft(e.target.value)}
                      onBlur={saveRelabel}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') { e.preventDefault(); saveRelabel() }
                        else if (e.key === 'Escape') { e.preventDefault(); cancelRelabel() }
                      }}
                      style={{
                        width: '100%',
                        fontSize: '0.85rem',
                        padding: '0.15rem 0.3rem',
                        background: 'var(--color-bg-secondary, rgba(255,255,255,0.05))',
                        border: '1px solid var(--color-border)',
                        borderRadius: '3px',
                        color: 'inherit',
                        textAlign: 'center'
                      }}
                    />
                  ) : (
                    <span
                      style={{ cursor: 'pointer' }}
                      title="Click to relabel"
                      onClick={() => startRelabel(c.character)}
                    >
                      {c.character}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <style>{`
        .icon-tile-actions {
          transition: opacity 0.15s;
        }
        .icon-tile:hover .icon-tile-actions {
          opacity: 1 !important;
        }
      `}</style>
    </div>
  )
}
