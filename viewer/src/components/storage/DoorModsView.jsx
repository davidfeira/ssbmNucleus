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
          className="intake-import-btn"
          style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
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

      <div className="patches-list">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading...</div>
        ) : mods.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            No door mods yet. Import a PNG image to use as the CSS character port door texture.
            The image will be automatically resized and the alpha mask applied.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.75rem' }}>
            {mods.map((mod) => (
              <div
                key={mod.id}
                onMouseEnter={playHoverSound}
                style={{
                  background: 'var(--color-surface, #2a2a4a)',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  border: '1px solid var(--color-border, #333)',
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <div style={{ aspectRatio: '128 / 200', background: '#111', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {mod.imageUrl ? (
                    <img
                      src={`${BACKEND_URL}${mod.imageUrl}`}
                      alt={mod.name}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  ) : (
                    <span style={{ color: '#666', fontSize: '2rem' }}>{(mod.name || '?')[0]}</span>
                  )}
                </div>
                <div style={{ padding: '0.4rem 0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.25rem' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--color-text, #eee)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {mod.name}
                  </span>
                  <button
                    style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem', border: '1px solid var(--color-border, #444)', background: 'transparent', color: '#888', borderRadius: '3px', cursor: 'pointer', flexShrink: 0 }}
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
    </div>
  )
}
