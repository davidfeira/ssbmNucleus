/**
 * IconGridModsView - List of imported CSS Icon Grid mods.
 *
 * Each mod is a zip of character portrait PNGs (with a screenshot/preview).
 * Provides import (zip upload) and delete actions; renders the screenshot as
 * the card image.
 */
import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'
import IconGridDetailView from './IconGridDetailView'

export default function IconGridModsView({ onDetailChange }) {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [selectedModId, setSelectedModId] = useState(null)

  const fetchMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/list`)
      const data = await res.json()
      if (data.success) {
        setMods(data.mods || [])
      } else {
        console.error('Failed to list icon grid mods:', data.error)
      }
    } catch (err) {
      console.error('Failed to list icon grid mods:', err)
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
    // Explicit hint so the unified pipeline skips costume/stage/patch detection
    formData.append('mod_type', 'css_icon_grid')

    try {
      const res = await fetch(`${API_URL}/import/file`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.success && data.type === 'menu_mod') {
        const mods = data.mods || (data.mod ? [data.mod] : [])
        const summary = mods.length > 1
          ? `✓ Imported ${mods.length} packs: ${mods.map(m => m.name).join(', ')}`
          : `✓ Imported ${mods[0]?.name || file.name}`
        setImportMessage(summary)
        await fetchMods()
      } else if (data.success) {
        setImportMessage(`Imported as ${data.type}, not icon grid.`)
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
      const res = await fetch(`${API_URL}/menus/css/icon_grid/delete/${mod.id}`, {
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

  if (selectedModId) {
    return (
      <IconGridDetailView
        modId={selectedModId}
        onBack={() => { setSelectedModId(null); onDetailChange?.(false) }}
        onModUpdated={(updated) => {
          setMods(prev => prev.map(m => m.id === updated.id ? { ...m, ...updated } : m))
        }}
      />
    )
  }

  return (
    <div className="icon-grid-mods">
      <div className="import-file-container">
        <label
          className={`intake-import-btn ${importing ? 'disabled' : ''}`}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start') }}
        >
          {importing ? 'Importing...' : 'Import Icon Grid Mod'}
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
          <div className="vault-empty">Loading...</div>
        ) : mods.length === 0 ? (
          <div className="vault-empty">
            No icon grid mods yet. Import a .zip to get started.
          </div>
        ) : (
          mods.map((mod) => (
            <div
              key={mod.id}
              className="patch-row clickable"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setSelectedModId(mod.id); onDetailChange?.(true) }}
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
              </div>

              <div className="patch-row-actions">
                <button
                  className="btn-build-iso btn-quiet"
                  onMouseEnter={playHoverSound}
                  onClick={(e) => { e.stopPropagation(); playSound('boop'); handleDelete(mod) }}
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
