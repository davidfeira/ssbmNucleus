import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { appConfirm } from '../../utils/appDialogs'
import { API_URL, BACKEND_URL } from '../../config'
import MenuModGrid from './MenuModGrid'
import MenuModEditModal from './MenuModEditModal'
import useMenuModEdit from './useMenuModEdit'

export default function DoorModsView() {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const edit = useMenuModEdit()

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

  const handleSave = async () => {
    const mod = edit.editing
    if (!mod) return
    edit.setSaving(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/doors/rename/${mod.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: edit.editName }),
      })
      const data = await res.json()
      if (!data.success) { alert(`Save failed: ${data.error}`); edit.setSaving(false); return }

      if (edit.newImage) {
        const fd = new FormData()
        fd.append('screenshot', edit.newImage)
        const ir = await fetch(`${API_URL}/menus/css/doors/${mod.id}/screenshot`, { method: 'POST', body: fd })
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
    a.href = `${API_URL}/menus/css/doors/${mod.id}/export`
    a.download = ''
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const handleDelete = async (mod) => {
    if (!await appConfirm(`Delete "${mod.name}"?`, {
      title: 'Delete Door Mod',
      confirmText: 'Delete',
    })) return
    edit.setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/doors/delete/${mod.id}`, { method: 'POST' })
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

      <MenuModGrid
        mods={mods}
        loading={loading}
        emptyText="No door mods yet. Import a PNG image to use as the CSS character port door texture. The image is stretched to the in-game 128×200 door and the original alpha mask is applied."
        thumb="tall"
        imgFit="fill"
        cacheBust={edit.cacheBust}
        onEditClick={edit.open}
      />

      <MenuModEditModal
        show={!!edit.editing}
        title="Edit Door"
        previewUrl={edit.editing?.imageUrl ? `${BACKEND_URL}${edit.editing.imageUrl}?v=${edit.cacheBust}` : null}
        thumb="tall"
        imgFit="fill"
        name={edit.editName}
        onNameChange={edit.setEditName}
        nameLabel="Door Name"
        editableImage
        imagePreview={edit.imagePreview}
        onImageChange={edit.handleImageChange}
        imageEditTitle="Replace the door texture"
        saving={edit.saving}
        deleting={edit.deleting}
        exporting={edit.exporting}
        onSave={handleSave}
        onExport={() => handleExport(edit.editing)}
        onDelete={() => handleDelete(edit.editing)}
        onCancel={edit.close}
      />
    </div>
  )
}
