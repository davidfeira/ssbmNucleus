import { useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import ConfirmDialog from '../shared/ConfirmDialog'

export default function CustomStageDetailView({ stage, onBack, onDelete, onRename, API_URL }) {
  const [editingName, setEditingName] = useState(false)
  const [nameValue, setNameValue] = useState(stage.name)
  const [saving, setSaving] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleSaveRename = async () => {
    const trimmed = nameValue.trim()
    if (!trimmed || trimmed === stage.name) {
      setEditingName(false)
      setNameValue(stage.name)
      return
    }
    setSaving(true)
    try {
      const response = await fetch(`${API_URL}/custom-stages/${stage.slug}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ newName: trimmed })
      })
      const data = await response.json()
      if (data.success) {
        setEditingName(false)
        onRename({ ...stage, name: trimmed })
      } else {
        alert(data.error || 'Rename failed')
      }
    } catch (err) {
      alert(`Rename error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/custom-stages/${stage.slug}/delete`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        onDelete()
      } else {
        alert(data.error || 'Delete failed')
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
      setShowConfirmDialog(false)
    }
  }

  const handleExport = () => {
    const link = document.createElement('a')
    link.href = `${API_URL}/custom-stages/${stage.slug}/export`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const bannerUrl = stage.has_banner
    ? `${API_URL}/custom-stages/${stage.slug}/banner`
    : null

  const iconUrl = stage.has_icon
    ? `${API_URL}/custom-stages/${stage.slug}/icon`
    : null

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        <button
          onClick={() => { playSound('back'); onBack(); }}
          className="back-button"
        >
          ← Back to Custom Stages
        </button>

        <div className="custom-stage-detail-header">
          {bannerUrl && (
            <img
              src={bannerUrl}
              alt={`${stage.name} banner`}
              className="custom-stage-banner"
            />
          )}
          {!bannerUrl && iconUrl && (
            <img
              src={iconUrl}
              alt={`${stage.name} icon`}
              className="custom-stage-banner"
            />
          )}

          <div className="custom-stage-title">
            {editingName ? (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  value={nameValue}
                  onChange={(e) => setNameValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveRename()
                    if (e.key === 'Escape') { setEditingName(false); setNameValue(stage.name) }
                  }}
                  autoFocus
                  className="edit-name-input"
                  disabled={saving}
                />
                <button className="mode-btn" onClick={handleSaveRename} disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button className="mode-btn" onClick={() => { setEditingName(false); setNameValue(stage.name) }}>
                  Cancel
                </button>
              </div>
            ) : (
              <h2>{stage.name}</h2>
            )}
          </div>
        </div>

        <div className="custom-stage-metadata">
          <div className="custom-stage-meta-row">
            <span className="custom-stage-meta-label">Source</span>
            <span>{stage.source === 'zip' ? 'Imported ZIP' : 'Project Scan'}</span>
          </div>
          <div className="custom-stage-meta-row">
            <span className="custom-stage-meta-label">Added</span>
            <span>{new Date(stage.date_added).toLocaleDateString()}</span>
          </div>
          {stage.series_id != null && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Series ID</span>
              <span>{stage.series_id}</span>
            </div>
          )}
          {stage.sound_bank != null && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Sound Bank</span>
              <span>{stage.sound_bank}</span>
            </div>
          )}
          {stage.dat_files && stage.dat_files.length > 0 && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Files</span>
              <span>{stage.dat_files.join(', ')}</span>
            </div>
          )}
        </div>

        <div className="custom-stage-actions">
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); setEditingName(true) }}
          >
            Rename
          </button>
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); handleExport() }}
            disabled={stage.source !== 'zip'}
            title={stage.source !== 'zip' ? 'Export only available for ZIP imports' : 'Download original ZIP'}
          >
            Export ZIP
          </button>
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); setShowConfirmDialog(true) }}
            style={{ background: 'var(--color-danger, #e53e3e)' }}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>

      <ConfirmDialog
        show={showConfirmDialog}
        title="Delete Custom Stage"
        message={`Are you sure you want to delete "${stage.name}"? This cannot be undone.`}
        confirmText="Delete"
        onConfirm={handleDelete}
        onCancel={() => setShowConfirmDialog(false)}
      />
    </div>
  )
}
