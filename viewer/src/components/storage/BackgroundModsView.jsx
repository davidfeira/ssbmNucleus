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
import MenuModGrid from './MenuModGrid'
import MenuModEditModal from './MenuModEditModal'
import useMenuModEdit from './useMenuModEdit'

export default function BackgroundModsView() {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const edit = useMenuModEdit()

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

  const handleSave = async () => {
    const mod = edit.editing
    if (!mod) return
    edit.setSaving(true)
    try {
      const res = await fetch(`${API_URL}/menus/background/update/${mod.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: edit.editName }),
      })
      const data = await res.json()
      if (!data.success) { alert(`Save failed: ${data.error}`); edit.setSaving(false); return }

      if (edit.newImage) {
        const fd = new FormData()
        fd.append('screenshot', edit.newImage)
        const ir = await fetch(`${API_URL}/menus/background/${mod.id}/screenshot`, { method: 'POST', body: fd })
        const idata = await ir.json()
        if (!idata.success) { alert(`Image upload failed: ${idata.error}`); edit.setSaving(false); return }
      }

      playSound('boop')
      edit.bumpCache()
      await fetchMods()
      edit.close()
    } catch (err) {
      alert(`Save error: ${err.message}`)
      edit.setSaving(false)
    }
  }

  const handleExport = (mod) => {
    if (!mod) return
    const a = document.createElement('a')
    a.href = `${API_URL}/menus/background/${mod.id}/export`
    a.download = ''
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const handleDelete = async (mod) => {
    if (!window.confirm(`Delete "${mod.name}"? This removes its files from your vault.`)) {
      return
    }
    edit.setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/menus/background/delete/${mod.id}`, {
        method: 'POST'
      })
      const data = await res.json()
      if (data.success) {
        playSound('boop')
        await fetchMods()
        edit.close()
      } else {
        alert(`Delete failed: ${data.error}`)
        edit.setDeleting(false)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
      edit.setDeleting(false)
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

  // Live copy of the mod being edited so the scene toggle reflects updates.
  const editingMod = edit.editing
    ? (mods.find(m => m.id === edit.editing.id) || edit.editing)
    : null

  return (
    <div className="icon-grid-mods">
      <div className="import-file-container">
        <label
          className={`intake-import-btn ${importing ? 'disabled' : ''}`}
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

      <MenuModGrid
        mods={mods}
        loading={loading}
        emptyText="No background mods yet. Import a .zip or .dat containing a MnSlChr or MnSlMap file to get started."
        thumb="wide"
        imgFit="cover"
        cacheBust={edit.cacheBust}
        getImageUrl={(mod) => mod.screenshotUrl || null}
        getMeta={(mod) => mod.description || null}
        onEditClick={edit.open}
      />

      <MenuModEditModal
        show={!!editingMod}
        title="Edit Background"
        previewUrl={editingMod?.screenshotUrl ? `${BACKEND_URL}${editingMod.screenshotUrl}?v=${edit.cacheBust}` : null}
        thumb="wide"
        imgFit="cover"
        name={edit.editName}
        onNameChange={edit.setEditName}
        nameLabel="Background Name"
        editableImage
        imagePreview={edit.imagePreview}
        onImageChange={edit.handleImageChange}
        imageEditTitle="Replace the preview screenshot"
        saving={edit.saving}
        deleting={edit.deleting}
        exporting={edit.exporting}
        onSave={handleSave}
        onExport={() => handleExport(editingMod)}
        onDelete={() => handleDelete(editingMod)}
        onCancel={edit.close}
        extra={editingMod && (
          <label
            className="mmod-toggle"
            title="When enabled, installs the background's camera, lighting, and fog settings alongside the model. Turn off if the background looks wrong on a different screen."
          >
            <input
              type="checkbox"
              checked={!!editingMod.includeScene}
              onChange={() => handleToggleScene(editingMod)}
            />
            Include Scene Settings
          </label>
        )}
      />
    </div>
  )
}
