/**
 * IconGridModsView - List of imported CSS Icon Grid mods.
 *
 * Each mod is a zip of character portrait PNGs (with a screenshot/preview).
 * Provides import (zip upload) and delete actions; renders the screenshot as
 * the card image.
 */
import { useEffect, useState, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { appConfirm } from '../../utils/appDialogs'
import { API_URL, BACKEND_URL } from '../../config'
import IconGridDetailView from './IconGridDetailView'
import MenuModGrid from './MenuModGrid'
import MenuModEditModal from './MenuModEditModal'
import useMenuModEdit from './useMenuModEdit'

export default function IconGridModsView({ onDetailChange }) {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [selectedModId, setSelectedModId] = useState(null)
  const edit = useMenuModEdit()

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

  const handleSave = async () => {
    const mod = edit.editing
    if (!mod) return
    edit.setSaving(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/update/${mod.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: edit.editName }),
      })
      const data = await res.json()
      if (!data.success) { alert(`Save failed: ${data.error}`); edit.setSaving(false); return }

      if (edit.newImage) {
        const fd = new FormData()
        fd.append('screenshot', edit.newImage)
        const ir = await fetch(`${API_URL}/menus/css/icon_grid/${mod.id}/screenshot`, { method: 'POST', body: fd })
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
    a.href = `${API_URL}/menus/css/icon_grid/${mod.id}/export`
    a.download = ''
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const handleDelete = async (mod) => {
    if (!await appConfirm(`Delete "${mod.name}"? This removes its files from your vault.`, {
      title: 'Delete Icon Grid',
      confirmText: 'Delete',
    })) {
      return
    }
    edit.setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/delete/${mod.id}`, {
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

  const openDetail = (mod) => {
    edit.close()
    setSelectedModId(mod.id)
    onDetailChange?.(true)
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

      <MenuModGrid
        mods={mods}
        loading={loading}
        emptyText="No icon grid mods yet. Import a .zip to get started."
        thumb="wide"
        imgFit="cover"
        getImageUrl={(mod) => mod.screenshotUrl || null}
        getMeta={(mod) => mod.description || null}
        cacheBust={edit.cacheBust}
        onCardClick={(mod) => { setSelectedModId(mod.id); onDetailChange?.(true) }}
        onEditClick={edit.open}
      />

      <MenuModEditModal
        show={!!edit.editing}
        title="Edit Icon Grid"
        previewUrl={edit.editing?.screenshotUrl ? `${BACKEND_URL}${edit.editing.screenshotUrl}?v=${edit.cacheBust}` : null}
        thumb="wide"
        imgFit="cover"
        name={edit.editName}
        onNameChange={edit.setEditName}
        nameLabel="Mod Name"
        editableImage
        imagePreview={edit.imagePreview}
        onImageChange={edit.handleImageChange}
        imageEditTitle="Replace the preview screenshot"
        saving={edit.saving}
        deleting={edit.deleting}
        exporting={edit.exporting}
        onSave={handleSave}
        onExport={() => handleExport(edit.editing)}
        onDelete={() => handleDelete(edit.editing)}
        onCancel={edit.close}
        actions={[
          {
            key: 'icons',
            label: 'Manage Icons',
            title: 'Open the per-character icon editor',
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
            ),
            onClick: () => openDetail(edit.editing),
          },
        ]}
      />
    </div>
  )
}
