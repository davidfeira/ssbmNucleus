/**
 * BackgroundModsView - List of imported background mods (shared CSS/SSS pool).
 *
 * Each mod is a background model/animation bundle extracted from a menu dat.
 * Provides import (.zip/.dat/.usd upload) and delete actions; renders
 * a screenshot as the card image when available.
 */
import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'

export default function BackgroundModsView() {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')

  const fetchMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/background/list`)
      const data = await res.json()
      if (data.success) {
        setMods(data.mods || [])
      } else {
        console.error('Failed to list background mods:', data.error)
      }
    } catch (err) {
      console.error('Failed to list background mods:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMods()
  }, [fetchMods])

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // reset so the same file can be re-picked
    if (!file) return

    setImporting(true)
    setImportMessage(`Importing ${file.name}...`)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/menus/background/import`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.success) {
        setImportMessage(`Imported ${data.mod?.name || file.name}`)
        await fetchMods()
      } else {
        setImportMessage(`Import failed: ${data.error}`)
      }
    } catch (err) {
      setImportMessage(`Import error: ${err.message}`)
    } finally {
      setImporting(false)
      setTimeout(() => setImportMessage(''), 4000)
    }
  }

  const handleDelete = async (mod) => {
    if (!window.confirm(`Delete "${mod.name}"? This removes its files from your vault.`)) {
      return
    }
    try {
      const res = await fetch(`${API_URL}/menus/background/delete/${mod.id}`, {
        method: 'POST'
      })
      const data = await res.json()
      if (data.success) {
        playSound('boop')
        await fetchMods()
      } else {
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    }
  }

  const handleToggleScene = async (mod) => {
    const newVal = !mod.includeScene
    try {
      const res = await fetch(`${API_URL}/menus/background/update/${mod.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ includeScene: newVal })
      })
      const data = await res.json()
      if (data.success) {
        playSound('boop')
        setMods(prev => prev.map(m => m.id === mod.id ? { ...m, includeScene: newVal } : m))
      }
    } catch (err) {
      console.error('Failed to toggle scene setting:', err)
    }
  }

  return (
    <div className="icon-grid-mods">
      <div className="import-file-container">
        <label
          className="intake-import-btn"
          style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start') }}
        >
          {importing ? 'Importing...' : 'Import Background Mod'}
          <input
            type="file"
            accept=".zip,.dat,.usd"
            onChange={handleImport}
            disabled={importing}
            style={{ display: 'none' }}
          />
        </label>
        {importMessage && (
          <div className={`import-message ${importMessage.includes('failed') || importMessage.includes('error') ? 'error' : 'success'}`}>
            {importMessage}
          </div>
        )}
      </div>

      <div className="patches-list">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Loading...
          </div>
        ) : mods.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            No background mods yet. Import a .zip or .dat containing a MnSlChr or MnSlMap file to get started.
          </div>
        ) : (
          mods.map((mod) => (
            <div
              key={mod.id}
              className="patch-row"
              onMouseEnter={playHoverSound}
              style={{ cursor: 'default' }}
            >
              <div className="patch-row-image">
                {mod.screenshotUrl ? (
                  <img
                    src={`${BACKEND_URL}${mod.screenshotUrl}`}
                    alt={mod.name}
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextSibling.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div className="patch-row-placeholder" style={{ display: mod.screenshotUrl ? 'none' : 'flex' }}>
                  {(mod.name || '?')[0]}
                </div>
              </div>

              <div className="patch-row-info">
                <h4 className="patch-row-name">{mod.name}</h4>
                {mod.description && (
                  <p className="patch-row-description">{mod.description}</p>
                )}
                <label
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '0.75rem', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                  title="When enabled, installs the background's camera, lighting, and fog settings alongside the model. Turn off if the background looks wrong on a different screen."
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={!!mod.includeScene}
                    onChange={() => handleToggleScene(mod)}
                    style={{ accentColor: 'var(--color-primary, #7c4dff)' }}
                  />
                  Include Scene Settings
                </label>
              </div>

              <div className="patch-row-actions">
                <button
                  className="btn-build-iso"
                  onMouseEnter={playHoverSound}
                  onClick={(e) => { e.stopPropagation(); playSound('boop'); handleDelete(mod) }}
                  style={{ background: 'transparent', border: '1px solid var(--color-border)' }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
