/**
 * PercentFontView - HUD typeface (IfAll) mods in the vault.
 *
 * Two faces of the same mod catalog, picked by `category`:
 *   'percent' — damage percent digits; accepts compiled IfAll mods
 *               (.zip/.dat/.usd) or digit glyph packs (0-9 + percent/HP).
 *   'readygo' — READY / GO! / GAME! word banners; accepts IfAll mods or
 *               word packs (ready.png, go.png... or Dolphin-hash names).
 * Compiled mods store every texture slot that differs from vanilla and may
 * appear in both categories.
 */
import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'
import PercentFontEditor from './PercentFontEditor'

export default function PercentFontView({ onDetailChange, category = 'percent' }) {
  const isWords = category === 'readygo'
  const noun = isWords ? 'Ready/Go Pack' : 'Percent Font'
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [editingMod, setEditingMod] = useState(null)   // mod open in the glyph editor
  const [cacheBust, setCacheBust] = useState(0)

  const fetchMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/percent/list?category=${category}`)
      const data = await res.json()
      if (data.success) setMods(data.mods || [])
    } catch (err) {
      console.error('Failed to list percent mods:', err)
    } finally {
      setLoading(false)
    }
  }, [category])

  useEffect(() => { fetchMods() }, [fetchMods])

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setImporting(true)
    setImportMessage(`Importing ${file.name}...`)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^.]+$/, ''))

    try {
      const res = await fetch(`${API_URL}/menus/percent/import`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.success) {
        const names = (data.mods || []).map(m => m.name).join(', ')
        setImportMessage(`Imported ${names || file.name}`)
        playSound('newSkin')
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

  const handleCreate = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/percent/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category }),
      })
      const data = await res.json()
      if (data.success) {
        playSound('newSkin')
        await fetchMods()
        // Drop straight into the glyph editor on the fresh mod
        setEditingMod(data.mod)
        onDetailChange?.(true)
      } else {
        setImportMessage(`Create failed: ${data.error}`)
        setTimeout(() => setImportMessage(''), 4000)
      }
    } catch (err) {
      setImportMessage(`Create error: ${err.message}`)
      setTimeout(() => setImportMessage(''), 4000)
    }
  }

  const handleDelete = async (mod) => {
    if (!window.confirm(`Delete "${mod.name}"?`)) return
    try {
      const res = await fetch(`${API_URL}/menus/percent/delete/${mod.id}`, { method: 'POST' })
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

  if (editingMod) {
    return (
      <PercentFontEditor
        mod={editingMod}
        mode={isWords ? 'words' : 'glyphs'}
        onBack={() => {
          setEditingMod(null)
          onDetailChange?.(false)
          setCacheBust(Date.now())
          fetchMods()
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
          {importing ? 'Importing...' : `Import ${noun}`}
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

      {loading ? (
        <div className="vault-empty">Loading...</div>
      ) : (
        <>
        {mods.length === 0 && (
          <div className="vault-empty">
            {isWords
              ? 'No Ready/Go/Game packs yet. Import an IfAll mod (.zip/.dat/.usd), a zip of banner images (ready/go/game...), or create one from scratch below.'
              : 'No percent font mods yet. Import an IfAll mod (.zip/.dat/.usd), a zip of digit images (0-9 + percent), or create one from scratch below.'}
          </div>
        )}
        <div className="mod-card-grid">
          {mods.map((mod) => (
            <div key={mod.id} className="mod-card" onMouseEnter={playHoverSound}>
              <div className="mod-card-preview">
                {mod.imageUrl ? (
                  <img
                    src={`${BACKEND_URL}${mod.imageUrl}${cacheBust ? `?v=${cacheBust}` : ''}`}
                    alt={mod.name}
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                ) : (
                  <span className="mod-card-monogram">{(mod.name || '?')[0]}</span>
                )}
                <button
                  className="mod-card-edit"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); setEditingMod(mod); onDetailChange?.(true) }}
                  title={isWords ? 'Edit individual banners (Ready, Go!, Game!...)' : 'Edit individual glyphs (digits, %, HP)'}
                >
                  ✎
                </button>
              </div>
              <div className="mod-card-footer">
                <span className="mod-card-name" title={mod.name}>{mod.name}</span>
                <button
                  className="mod-card-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); handleDelete(mod) }}
                >
                  Del
                </button>
              </div>
            </div>
          ))}
          <div
            className="mod-card mod-card--create"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); handleCreate() }}
            title={isWords
              ? 'Start from the vanilla banners and edit each one'
              : 'Start from the vanilla percent font and edit each glyph'}
          >
            <div className="mod-card-preview">
              <span className="mod-card-monogram">+</span>
            </div>
            <div className="mod-card-footer">
              <span className="mod-card-name">New {noun}</span>
            </div>
          </div>
        </div>
        </>
      )}
    </div>
  )
}
