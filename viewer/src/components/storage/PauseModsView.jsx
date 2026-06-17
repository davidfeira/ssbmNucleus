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
import { appConfirm, appPrompt } from '../../utils/appDialogs'
import { API_URL, BACKEND_URL } from '../../config'
import { useInGameTest } from '../../hooks/useInGameTest'
import InGameTestPanel from '../shared/InGameTestPanel'
import PauseTextureEditor from './PauseTextureEditor'
import MenuModGrid from './MenuModGrid'
import MenuModEditModal from './MenuModEditModal'
import useMenuModEdit from './useMenuModEdit'

export default function PauseModsView({ onDetailChange }) {
  const [mods, setMods] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [captureTarget, setCaptureTarget] = useState(null)  // mod being captured
  const [editingMod, setEditingMod] = useState(null)        // mod open in the texture editor
  const [draftMode, setDraftMode] = useState(false)         // editor is on an uncommitted draft
  const [cacheBust, setCacheBust] = useState(0)
  const test = useInGameTest()
  const edit = useMenuModEdit()

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

  // "New" creates an uncommitted DRAFT (not in the vault) and drops straight
  // into the editor. It only lands in the vault when the user saves it.
  const handleCreate = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/pause/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft: true }),
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
    const name = await appPrompt('Name this pause mod:', {
      title: 'Save Pause Mod',
      defaultValue: mod.name || 'New Pause Mod',
      confirmText: 'Save',
    })
    if (name === null) return  // cancelled — stay in the editor
    try {
      const res = await fetch(`${API_URL}/menus/pause/${mod.id}/save`, {
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
    if (!await appConfirm('Discard this unsaved pause mod?', {
      title: 'Discard Draft',
      confirmText: 'Discard',
    })) return
    try {
      await fetch(`${API_URL}/menus/pause/${mod.id}/discard`, { method: 'POST' })
    } catch { /* best effort */ }
    playSound('back')
    closeEditor()
  }

  // Rename / save an existing mod from the edit modal.
  const handleSave = async () => {
    const mod = edit.editing
    if (!mod) return
    edit.setSaving(true)
    try {
      const res = await fetch(`${API_URL}/menus/pause/${mod.id}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: edit.editName }),
      })
      const data = await res.json()
      if (!data.success) { alert(`Save failed: ${data.error}`); edit.setSaving(false); return }

      if (edit.newImage) {
        const fd = new FormData()
        fd.append('screenshot', edit.newImage)
        const ir = await fetch(`${API_URL}/menus/pause/${mod.id}/screenshot`, { method: 'POST', body: fd })
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
    a.href = `${API_URL}/menus/pause/${mod.id}/export`
    a.download = ''
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const handleDelete = async (mod) => {
    if (!await appConfirm(`Delete "${mod.name}"?`, {
      title: 'Delete Pause Mod',
      confirmText: 'Delete',
    })) return
    edit.setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/menus/pause/delete/${mod.id}`, { method: 'POST' })
      const data = await res.json()
      if (data.success) { playSound('boop'); await fetchMods(); edit.close() }
      else { alert(`Delete failed: ${data.error}`); edit.setDeleting(false) }
    } catch (err) {
      alert(`Delete error: ${err.message}`); edit.setDeleting(false)
    }
  }

  const openTextureEditor = (mod) => {
    edit.close()
    setEditingMod(mod)
    setDraftMode(false)
    onDetailChange?.(true)
  }

  if (editingMod) {
    return (
      <PauseTextureEditor
        mod={editingMod}
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

      <MenuModGrid
        mods={mods}
        loading={loading}
        emptyText="No pause screen mods yet. Import a GmPause mod (.zip/.dat/.usd), upload a picture for the central pause graphic, or create one from scratch below."
        thumb="wide"
        imgFit="contain"
        cacheBust={`${cacheBust}-${edit.cacheBust}`}
        onEditClick={edit.open}
        createCard={{
          label: 'New Pause Mod',
          title: 'Start from the vanilla pause screen and edit each texture',
          onClick: handleCreate,
        }}
      />

      <MenuModEditModal
        show={!!edit.editing}
        title="Edit Pause Mod"
        previewUrl={edit.editing?.imageUrl ? `${BACKEND_URL}${edit.editing.imageUrl}?v=${cacheBust}-${edit.cacheBust}` : null}
        thumb="wide"
        imgFit="contain"
        name={edit.editName}
        onNameChange={edit.setEditName}
        nameLabel="Pause Mod Name"
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
            label: 'Edit Textures',
            title: 'Edit individual pause screen textures',
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            ),
            onClick: () => openTextureEditor(edit.editing),
          },
          {
            key: 'capture',
            label: 'Capture Screenshot',
            title: "Capture a live in-game pause screenshot as this mod's preview",
            disabled: test.testingInGame,
            icon: (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            ),
            onClick: () => { const m = edit.editing; edit.close(); handleCapture(m) },
          },
        ]}
      />
    </div>
  )
}
