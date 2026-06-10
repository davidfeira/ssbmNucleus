/**
 * PauseModsView - Pause screen (GmPause) mods in the vault.
 *
 * Accepts a compiled GmPause mod (.zip/.dat/.usd) or a plain picture.
 * Compiled mods reproduce every replaced texture; a picture replaces the
 * central pause graphic. Each mod card can capture a LIVE in-game preview:
 * the backend builds a vanilla+mod ISO, pauses a solo match, and saves the
 * shot as the mod's screenshot.
 */
import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'
import { useInGameTest } from '../../hooks/useInGameTest'
import InGameTestPanel from '../shared/InGameTestPanel'
import PauseTextureEditor from './PauseTextureEditor'

export default function PauseModsView({ onDetailChange }) {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [captureTarget, setCaptureTarget] = useState(null)  // mod being captured
  const [editingMod, setEditingMod] = useState(null)        // mod open in the texture editor
  const [cacheBust, setCacheBust] = useState(0)
  const test = useInGameTest()

  const fetchMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/pause/list`)
      const data = await res.json()
      if (data.success) setMods(data.mods || [])
    } catch (err) {
      console.error('Failed to list pause mods:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchMods() }, [fetchMods])

  // A finished capture already saved the screenshot backend-side — refresh the
  // cards and bust the preview cache so the new shot shows up.
  useEffect(() => {
    if (test.testResult?.captured) {
      fetchMods()
      setCacheBust(Date.now())
    }
  }, [test.testResult, fetchMods])

  const handleCapture = (mod) => {
    setCaptureTarget(mod)
    test.capturePauseScreenshot({ modId: mod.id, name: mod.name })
  }

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
      const res = await fetch(`${API_URL}/menus/pause/import`, {
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
      const res = await fetch(`${API_URL}/menus/pause/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      const data = await res.json()
      if (data.success) {
        playSound('newSkin')
        await fetchMods()
        // Drop straight into the texture editor on the fresh mod
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
      const res = await fetch(`${API_URL}/menus/pause/delete/${mod.id}`, { method: 'POST' })
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
      <PauseTextureEditor
        mod={editingMod}
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
          {importing ? 'Importing...' : 'Import Pause Mod'}
          <input
            type="file"
            accept=".zip,.dat,.usd,image/png,image/jpeg,image/webp"
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

      {captureTarget && (test.testingInGame || test.testResult || test.testError) && (
        <div className="vault-panel-box">
          <InGameTestPanel
            test={test}
            onStart={() => test.capturePauseScreenshot({ modId: captureTarget.id, name: captureTarget.name })}
            label="Capture Pause Screenshot"
          />
        </div>
      )}

      {loading ? (
        <div className="vault-empty">Loading...</div>
      ) : (
        <>
        {mods.length === 0 && (
          <div className="vault-empty">
            No pause screen mods yet. Import a GmPause mod (.zip/.dat/.usd), upload a
            picture for the central pause graphic, or create one from scratch below.
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
                  title="Edit individual pause screen textures"
                >
                  ✎
                </button>
              </div>
              <div className="mod-card-footer">
                <span className="mod-card-name" title={mod.name}>{mod.name}</span>
                <button
                  className="mod-card-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => { if (!test.testingInGame) { playSound('boop'); handleCapture(mod) } }}
                  disabled={test.testingInGame}
                  title="Capture a live in-game pause screenshot as this mod's preview"
                >
                  📸
                </button>
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
            title="Start from the vanilla pause screen and edit each texture"
          >
            <div className="mod-card-preview">
              <span className="mod-card-monogram">+</span>
            </div>
            <div className="mod-card-footer">
              <span className="mod-card-name">New Pause Mod</span>
            </div>
          </div>
        </div>
        </>
      )}
    </div>
  )
}
