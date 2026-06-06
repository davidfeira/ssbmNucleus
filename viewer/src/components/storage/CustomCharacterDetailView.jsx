import { useState, useEffect } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import ConfirmDialog from '../shared/ConfirmDialog'
import InGameTestPanel from '../shared/InGameTestPanel'
import { useInGameTest } from '../../hooks/useInGameTest'

export default function CustomCharacterDetailView({ character, onBack, onDelete, onRename, API_URL }) {
  const [editingName, setEditingName] = useState(false)
  const [nameValue, setNameValue] = useState(character.name)
  const [saving, setSaving] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [detail, setDetail] = useState(null)
  const inGameTest = useInGameTest()

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await fetch(`${API_URL}/custom-characters/${character.slug}/detail`)
        const data = await response.json()
        if (data.success) setDetail(data.detail)
      } catch (err) {
        console.error('Failed to fetch character detail:', err)
      }
    }
    fetchDetail()
  }, [character.slug, API_URL])

  const handleSaveRename = async () => {
    const trimmed = nameValue.trim()
    if (!trimmed || trimmed === character.name) {
      setEditingName(false)
      setNameValue(character.name)
      return
    }
    setSaving(true)
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ newName: trimmed })
      })
      const data = await response.json()
      if (data.success) {
        setEditingName(false)
        onRename({ ...character, name: trimmed })
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
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/delete`, {
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
    link.href = `${API_URL}/custom-characters/${character.slug}/export`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const iconUrl = character.has_css_icon
    ? `${API_URL}/custom-characters/${character.slug}/icon`
    : null

  const costumes = detail?.costumes || []

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        <button
          onClick={() => { playSound('back'); onBack(); }}
          className="back-button"
        >
          ← Back to Custom Characters
        </button>

        <div className="custom-stage-detail-header">
          {iconUrl && (
            <img
              src={iconUrl}
              alt={`${character.name} icon`}
              className="custom-stage-banner"
              style={{ width: '128px', imageRendering: 'pixelated' }}
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
                    if (e.key === 'Escape') { setEditingName(false); setNameValue(character.name) }
                  }}
                  autoFocus
                  className="edit-name-input"
                  disabled={saving}
                />
                <button className="mode-btn" onClick={handleSaveRename} disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button className="mode-btn" onClick={() => { setEditingName(false); setNameValue(character.name) }}>
                  Cancel
                </button>
              </div>
            ) : (
              <h2>{character.name}</h2>
            )}
          </div>
        </div>

        <div className="custom-stage-metadata">
          <div className="custom-stage-meta-row">
            <span className="custom-stage-meta-label">Source</span>
            <span>{character.source === 'zip' ? 'Imported ZIP' : 'ISO Scan'}</span>
          </div>
          <div className="custom-stage-meta-row">
            <span className="custom-stage-meta-label">Added</span>
            <span>{new Date(character.date_added).toLocaleDateString()}</span>
          </div>
          {detail?.series_id != null && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Series ID</span>
              <span>{detail.series_id}</span>
            </div>
          )}
          <div className="custom-stage-meta-row">
            <span className="custom-stage-meta-label">Costumes</span>
            <span>{costumes.length}</span>
          </div>
          {detail?.can_wall_jump && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Wall Jump</span>
              <span>Yes</span>
            </div>
          )}
          {detail?.files?.fighterDataPath && (
            <div className="custom-stage-meta-row">
              <span className="custom-stage-meta-label">Fighter File</span>
              <span>{detail.files.fighterDataPath}</span>
            </div>
          )}
        </div>

        {costumes.length > 0 && (
          <div className="custom-char-costumes">
            <h3 style={{ marginBottom: 'var(--space-3)', color: 'var(--color-text-primary)' }}>Costumes</h3>
            <div className="custom-char-costume-grid">
              {costumes.map((costume) => (
                <div key={costume.index} className="custom-char-costume-card">
                  {costume.csp_url ? (
                    <img
                      src={costume.csp_url}
                      alt={costume.name}
                      className="custom-char-csp"
                    />
                  ) : (
                    <div className="custom-char-csp-placeholder">
                      {costume.name[0]}
                    </div>
                  )}
                  <div className="custom-char-costume-info">
                    {costume.stock_url && (
                      <img
                        src={costume.stock_url}
                        alt="stock"
                        className="custom-char-stock"
                      />
                    )}
                    <span className="custom-char-costume-name">{costume.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
            disabled={character.source !== 'zip'}
            title={character.source !== 'zip' ? 'Export only available for ZIP imports' : 'Download original ZIP'}
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

        {/* Test In Game */}
        <div className="custom-stage-test" style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)', textAlign: 'center' }}>
          <InGameTestPanel
            test={inGameTest}
            onStart={() => inGameTest.startCustomCharacterTest({ slug: character.slug, name: character.name })}
          />
        </div>
      </div>

      <ConfirmDialog
        show={showConfirmDialog}
        title="Delete Custom Character"
        message={`Are you sure you want to delete "${character.name}"? This cannot be undone.`}
        confirmText="Delete"
        onConfirm={handleDelete}
        onCancel={() => setShowConfirmDialog(false)}
      />
    </div>
  )
}
