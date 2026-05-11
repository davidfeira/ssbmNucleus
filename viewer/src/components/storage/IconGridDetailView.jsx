/**
 * IconGridDetailView - Labeled-icon view for a CSS icon grid mod.
 *
 * Fetches the normalized mod payload from /menus/css/icon_grid/<mod_id>/icons.
 * Renders the screenshot, an editable title, and one tile per labeled
 * character (normal + selected variants).
 */
import { useEffect, useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'

export default function IconGridDetailView({ modId, onBack, onModUpdated }) {
  const [mod, setMod] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingName, setEditingName] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const [savingName, setSavingName] = useState(false)
  const [relabelChar, setRelabelChar] = useState(null) // character currently being relabeled
  const [relabelDraft, setRelabelDraft] = useState('')

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

  const icons = mod?.icons || []

  return (
    <div className="icon-grid-detail" style={{ width: '100%' }}>
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

          <div style={{ color: 'var(--color-text-muted)', marginBottom: '0.75rem', fontSize: '0.9rem' }}>
            {icons.length} icon{icons.length === 1 ? '' : 's'}
          </div>

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
                style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: '6px',
                  padding: '0.5rem',
                  background: 'var(--color-bg-secondary, rgba(255,255,255,0.03))'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '80px' }}>
                  {c.iconUrl && (
                    <img
                      src={`${BACKEND_URL}${c.iconUrl}`}
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
    </div>
  )
}
