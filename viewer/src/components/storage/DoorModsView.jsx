import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'

export default function DoorModsView() {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')

  const fetchMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/doors/list`)
      const data = await res.json()
      if (data.success) setMods(data.mods || [])
    } catch (err) {
      console.error('Failed to list door mods:', err)
    } finally {
      setLoading(false)
    }
  }, [])

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
      const res = await fetch(`${API_URL}/menus/css/doors/import`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.success) {
        setImportMessage(`Imported ${data.mod?.name || file.name}`)
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

  const handleDelete = async (mod) => {
    if (!window.confirm(`Delete "${mod.name}"?`)) return
    try {
      const res = await fetch(`${API_URL}/menus/css/doors/delete/${mod.id}`, { method: 'POST' })
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

  return (
    <div className="icon-grid-mods">
      <div className="import-file-container">
        <label
          className={`intake-import-btn ${importing ? 'disabled' : ''}`}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start') }}
        >
          {importing ? 'Importing...' : 'Import Door Texture'}
          <input
            type="file"
            accept="image/png,image/jpeg,image/*"
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
      ) : mods.length === 0 ? (
        <div className="vault-empty">
          No door mods yet. Import a PNG image to use as the CSS character port door texture.
          The image will be automatically resized and the alpha mask applied.
        </div>
      ) : (
        <div className="mod-card-grid">
          {mods.map((mod) => (
            <div key={mod.id} className="mod-card mod-card--tall" onMouseEnter={playHoverSound}>
              <div className="mod-card-preview">
                {mod.imageUrl ? (
                  <img src={`${BACKEND_URL}${mod.imageUrl}`} alt={mod.name} />
                ) : (
                  <span className="mod-card-monogram">{(mod.name || '?')[0]}</span>
                )}
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
        </div>
      )}
    </div>
  )
}
