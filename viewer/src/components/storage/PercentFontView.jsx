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
import { appConfirm, appPrompt } from '../../utils/appDialogs'
import { API_URL, BACKEND_URL } from '../../config'
import PercentFontEditor from './PercentFontEditor'
import MenuModGrid from './MenuModGrid'
import MenuModEditModal from './MenuModEditModal'
import useMenuModEdit from './useMenuModEdit'

export default function PercentFontView({ onDetailChange, category = 'percent' }) {
  const isWords = category === 'readygo'
  const noun = isWords ? 'Ready/Go Pack' : 'Percent Font'
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [editingMod, setEditingMod] = useState(null)   // mod open in the glyph editor
  const [draftMode, setDraftMode] = useState(false)    // editor is on an uncommitted draft
  const [cacheBust, setCacheBust] = useState(0)
  const edit = useMenuModEdit()

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

  // "New" creates an uncommitted DRAFT (not in the vault) and drops straight
  // into the editor. It only lands in the vault when the user saves it.
  const handleCreate = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/percent/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, draft: true }),
      })
      const data = await res.json()
      if (data.success) {
        playSound('newSkin')
        setEditingMod(data.mod)
        setDraftMode(true)
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

  const closeEditor = () => {
    setEditingMod(null)
    setDraftMode(false)
    onDetailChange?.(false)
    setCacheBust(Date.now())
    fetchMods()
  }

  const commitDraft = async () => {
    const mod = editingMod
    if (!mod) return
    const name = await appPrompt(`Name this ${noun.toLowerCase()}:`, {
      title: `Save ${noun}`,
      defaultValue: mod.name || `New ${noun}`,
      confirmText: 'Save',
    })
    if (name === null) return
    try {
      const res = await fetch(`${API_URL}/menus/percent/${mod.id}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() || mod.name }),
      })
      const data = await res.json()
      if (data.success) { playSound('newSkin'); closeEditor() }
      else alert(`Save failed: ${data.error}`)
    } catch (err) {
      alert(`Save error: ${err.message}`)
    }
  }

  const discardDraft = async () => {
    const mod = editingMod
    if (!mod) return
    if (!await appConfirm(`Discard this unsaved ${noun.toLowerCase()}?`, {
      title: 'Discard Draft',
      confirmText: 'Discard',
    })) return
    try {
      await fetch(`${API_URL}/menus/percent/${mod.id}/discard`, { method: 'POST' })
    } catch { /* best effort */ }
    playSound('back')
    closeEditor()
  }

  const handleSave = async () => {
    const mod = edit.editing
    if (!mod) return
    edit.setSaving(true)
    try {
      const res = await fetch(`${API_URL}/menus/percent/${mod.id}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: edit.editName }),
      })
      const data = await res.json()
      if (!data.success) { alert(`Save failed: ${data.error}`); edit.setSaving(false); return }

      if (edit.newImage) {
        const fd = new FormData()
        fd.append('screenshot', edit.newImage)
        const ir = await fetch(`${API_URL}/menus/percent/${mod.id}/screenshot`, { method: 'POST', body: fd })
        const idata = await ir.json()
        if (!idata.success) { alert(`Image upload failed: ${idata.error}`); edit.setSaving(false); return }
      }

      playSound('boop'); edit.bumpCache(); await fetchMods(); edit.close()
    } catch (err) {
      alert(`Save error: ${err.message}`); edit.setSaving(false)
    }
  }

  const handleExport = (mod) => {
    if (!mod) return
    const a = document.createElement('a')
    a.href = `${API_URL}/menus/percent/${mod.id}/export`
    a.download = ''
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const handleDelete = async (mod) => {
    if (!await appConfirm(`Delete "${mod.name}"?`, {
      title: `Delete ${noun}`,
      confirmText: 'Delete',
    })) return
    edit.setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/menus/percent/delete/${mod.id}`, { method: 'POST' })
      const data = await res.json()
      if (data.success) { playSound('boop'); await fetchMods(); edit.close() }
      else { alert(`Delete failed: ${data.error}`); edit.setDeleting(false) }
    } catch (err) {
      alert(`Delete error: ${err.message}`); edit.setDeleting(false)
    }
  }

  const openGlyphEditor = (mod) => {
    edit.close()
    setEditingMod(mod)
    setDraftMode(false)
    onDetailChange?.(true)
  }

  if (editingMod) {
    return (
      <PercentFontEditor
        mod={editingMod}
        mode={isWords ? 'words' : 'glyphs'}
        isDraft={draftMode}
        onSaveDraft={commitDraft}
        onDiscardDraft={discardDraft}
        onBack={closeEditor}
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

      <MenuModGrid
        mods={mods}
        loading={loading}
        emptyText={isWords
          ? 'No Ready/Go/Game packs yet. Import an IfAll mod (.zip/.dat/.usd), a zip of banner images (ready/go/game...), or create one from scratch below.'
          : 'No percent font mods yet. Import an IfAll mod (.zip/.dat/.usd), a zip of digit images (0-9 + percent), or create one from scratch below.'}
        thumb="wide"
        imgFit="contain"
        cacheBust={`${cacheBust}-${edit.cacheBust}`}
        onEditClick={edit.open}
        createCard={{
          label: `New ${noun}`,
          title: isWords
            ? 'Start from the vanilla banners and edit each one'
            : 'Start from the vanilla percent font and edit each glyph',
          onClick: handleCreate,
        }}
      />

      <MenuModEditModal
        show={!!edit.editing}
        title={`Edit ${noun}`}
        previewUrl={edit.editing?.imageUrl ? `${BACKEND_URL}${edit.editing.imageUrl}?v=${cacheBust}-${edit.cacheBust}` : null}
        thumb="wide"
        imgFit="contain"
        name={edit.editName}
        onNameChange={edit.setEditName}
        nameLabel={`${noun} Name`}
        editableImage
        imagePreview={edit.imagePreview}
        onImageChange={edit.handleImageChange}
        imageEditTitle="Upload a custom preview screenshot"
        saving={edit.saving}
        deleting={edit.deleting}
        exporting={edit.exporting}
        onSave={handleSave}
        onExport={() => handleExport(edit.editing)}
        onDelete={() => handleDelete(edit.editing)}
        onCancel={edit.close}
        actions={[
          {
            key: 'edit',
            label: isWords ? 'Edit Banners' : 'Edit Glyphs',
            title: isWords ? 'Edit individual banners (Ready, Go!, Game!...)' : 'Edit individual glyphs (digits, %, HP)',
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            ),
            onClick: () => openGlyphEditor(edit.editing),
          },
        ]}
      />
    </div>
  )
}
