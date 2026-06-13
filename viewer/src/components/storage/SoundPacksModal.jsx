import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { getAppContentPortalTarget } from './appContentPortal'
import { CloseIcon } from '../shared/Icons'
import { playSound, playHoverSound } from '../../utils/sounds'
import SoundBankModal from './SoundBankModal'

/**
 * Sound pack manager for a vanilla character: a character can have any
 * number of alternate sound packs in the vault. Each pack is edited in
 * the SoundBankModal browser; packs are installed into a project as an
 * explicit action (installMode) — nothing applies automatically.
 *
 * Zelda and Sheik share one bank, so they share one pack list.
 */
export default function SoundPacksModal({ show, character, displayName, API_URL, onClose, installMode = false }) {
  const [packs, setPacks] = useState([])
  const [installed, setInstalled] = useState(null)
  const [projectOpen, setProjectOpen] = useState(false)
  const [sharedWith, setSharedWith] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)
  const [editingPack, setEditingPack] = useState(null)
  const messageTimerRef = useRef(null)

  const base = `${API_URL}/storage/characters/${encodeURIComponent(character)}/sound-packs`

  const fetchPacks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(base)
      const data = await response.json()
      if (data.success) {
        setPacks(data.packs)
        setInstalled(data.installed)
        setProjectOpen(data.project_open)
        setSharedWith(data.shared_with)
      } else {
        setError(data.error || 'Failed to load sound packs')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [base])

  useEffect(() => {
    if (show) {
      fetchPacks()
    } else {
      setCreating(false)
      setNewName('')
      setConfirmDeleteId(null)
      setEditingPack(null)
    }
  }, [show, fetchPacks])

  useEffect(() => () => clearTimeout(messageTimerRef.current), [])

  const flashMessage = (text) => {
    setMessage(text)
    clearTimeout(messageTimerRef.current)
    messageTimerRef.current = setTimeout(() => setMessage(''), 4000)
  }

  const handleCreate = async () => {
    const name = newName.trim()
    if (!name) return
    setBusy(true)
    try {
      const response = await fetch(`${base}/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        setCreating(false)
        setNewName('')
        await fetchPacks()
        // jump straight into editing the new pack
        setEditingPack({ id: data.id, name: data.name })
      } else {
        flashMessage(`Create failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Create error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async (pack) => {
    playSound('back')
    setBusy(true)
    try {
      const response = await fetch(`${base}/${pack.id}/delete`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        flashMessage(`Deleted "${pack.name}"`)
        await fetchPacks()
      } else {
        flashMessage(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Delete error: ${err.message}`)
    } finally {
      setConfirmDeleteId(null)
      setBusy(false)
    }
  }

  const handleInstall = async (pack) => {
    playSound('start')
    setBusy(true)
    flashMessage(`Installing "${pack.name}" into the project…`)
    try {
      const response = await fetch(`${base}/${pack.id}/install`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        flashMessage(`Installed "${pack.name}" — it ships with this project's ISO`)
        setInstalled(data.installed)
      } else {
        flashMessage(`Install failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Install error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  const handleUninstall = async () => {
    playSound('back')
    setBusy(true)
    flashMessage('Restoring original sounds…')
    try {
      const response = await fetch(`${base}/uninstall`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        flashMessage('Original sounds restored in this project')
        setInstalled(null)
      } else {
        flashMessage(`Restore failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Restore error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  if (!show) return null

  const canInstall = installMode && projectOpen

  const modal = (
    <div className="sp-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="sp-modal">
        <div className="sp-header">
          <div className="sp-title">
            <span className="sp-title-label">Sound Packs</span>
            <span className="sp-title-char">{displayName || character}</span>
          </div>
          <button className="sp-close-btn" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="sp-hint">
          {canInstall
            ? 'Pick which sound pack this project uses — installing applies it to this build only.'
            : 'Build alternate voice/SFX packs for this character. Install them per project from the Install tab.'}
          {sharedWith && ' Zelda and Sheik share one sound bank.'}
        </div>

        {message && <div className="sp-message">{message}</div>}

        <div className="sp-list">
          {loading ? (
            <div className="sp-empty">Loading sound packs…</div>
          ) : error ? (
            <div className="sp-empty sp-error">{error}</div>
          ) : (
            <>
              {canInstall && (
                <div className={`sp-row sp-row--original ${installed == null ? 'sp-row--installed' : ''}`}>
                  <span className="sp-pack-name">Original Sounds</span>
                  <span className="sp-pack-meta">vanilla bank</span>
                  <span className="sp-actions">
                    {installed == null ? (
                      <span className="sp-installed-badge">✓ In this project</span>
                    ) : (
                      <button
                        className="sp-action-btn sp-install-btn"
                        onMouseEnter={playHoverSound}
                        onClick={handleUninstall}
                        disabled={busy}
                      >
                        Restore
                      </button>
                    )}
                  </span>
                </div>
              )}

              {packs.map(pack => (
                <div
                  key={pack.id}
                  className={`sp-row ${canInstall && installed === pack.id ? 'sp-row--installed' : ''}`}
                >
                  <span className="sp-pack-name" title={pack.name}>{pack.name}</span>
                  <span className="sp-pack-meta">
                    {pack.modified_count} sound{pack.modified_count === 1 ? '' : 's'} replaced
                  </span>
                  <span className="sp-actions">
                    {canInstall && (installed === pack.id ? (
                      <span className="sp-installed-badge">✓ In this project</span>
                    ) : (
                      <button
                        className="sp-action-btn sp-install-btn"
                        onMouseEnter={playHoverSound}
                        onClick={() => handleInstall(pack)}
                        disabled={busy}
                        title="Install this pack into the open project"
                      >
                        Install
                      </button>
                    ))}
                    <button
                      className="sp-action-btn"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); setEditingPack(pack); }}
                      disabled={busy}
                      title="Browse and replace this pack's sounds"
                    >
                      Edit
                    </button>
                    {confirmDeleteId === pack.id ? (
                      <button
                        className="sp-action-btn sp-delete-btn sp-delete-confirm"
                        onMouseEnter={playHoverSound}
                        onClick={() => handleDelete(pack)}
                        disabled={busy}
                      >
                        Delete?
                      </button>
                    ) : (
                      <button
                        className="sp-action-btn sp-delete-btn"
                        onMouseEnter={playHoverSound}
                        onClick={() => { playSound('boop'); setConfirmDeleteId(pack.id); }}
                        disabled={busy}
                        title="Delete this pack from the vault"
                      >
                        ✕
                      </button>
                    )}
                  </span>
                </div>
              ))}

              {packs.length === 0 && (
                <div className="sp-empty">
                  No sound packs yet — create one to start replacing
                  {' '}{displayName || character}&apos;s voice and sound effects.
                </div>
              )}
            </>
          )}
        </div>

        <div className="sp-footer">
          {creating ? (
            <div className="sp-create-row">
              <input
                className="sp-name-input"
                autoFocus
                placeholder="Pack name (e.g. Anime Voice)"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreate()
                  if (e.key === 'Escape') { setCreating(false); setNewName('') }
                }}
                disabled={busy}
              />
              <button
                className="sp-action-btn sp-install-btn"
                onClick={handleCreate}
                disabled={busy || !newName.trim()}
              >
                Create
              </button>
              <button
                className="sp-action-btn"
                onClick={() => { playSound('back'); setCreating(false); setNewName('') }}
                disabled={busy}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              className="sp-new-pack-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setCreating(true); }}
              disabled={busy || loading}
            >
              + New Sound Pack
            </button>
          )}
        </div>
      </div>

      <style>{SOUND_PACKS_STYLES}</style>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return (
    <>
      {portalTarget ? createPortal(modal, portalTarget) : modal}
      <SoundBankModal
        show={editingPack !== null}
        displayName={`${displayName || character} — ${editingPack?.name || ''}`}
        endpoint={`storage/characters/${encodeURIComponent(character)}/sound-packs/${editingPack?.id}/audio`}
        hint="Replace any sound with a WAV/MP3 — edits are saved into this pack."
        API_URL={API_URL}
        onClose={() => { setEditingPack(null); fetchPacks() }}
      />
    </>
  )
}

const SOUND_PACKS_STYLES = `
        .sp-overlay {
          position: absolute;
          inset: 0;
          background: rgba(6, 12, 20, 0.92);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: calc(var(--z-modal) + 35);
          padding: var(--page-block-padding) var(--modal-inline-padding);
          overflow: auto;
          overscroll-behavior: contain;
        }

        .sp-modal {
          width: min(100%, 560px);
          max-height: min(100%, var(--modal-max-height));
          background: linear-gradient(
            165deg,
            var(--color-bg-elevated) 0%,
            var(--color-bg-base) 40%,
            var(--color-bg-deep) 100%
          );
          border: 1px solid var(--color-cyan);
          border-radius: var(--radius-2xl);
          box-shadow:
            var(--shadow-xl),
            0 0 80px rgba(0, 0, 0, 0.5),
            0 0 24px rgba(125, 211, 232, 0.12);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          margin: auto;
        }

        .sp-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-3) var(--space-6);
          background: rgba(0, 0, 0, 0.15);
          border-bottom: 1px solid var(--color-border-subtle);
          flex-shrink: 0;
        }

        .sp-title {
          display: flex;
          align-items: baseline;
          gap: var(--space-3);
          min-width: 0;
        }

        .sp-title-label {
          font-size: var(--text-lg);
          font-weight: 700;
          color: var(--color-text-primary);
        }

        .sp-title-char {
          color: var(--color-cyan);
          font-weight: 600;
        }

        .sp-close-btn {
          background: transparent;
          border: none;
          color: var(--color-text-secondary);
          cursor: pointer;
          display: flex;
          padding: var(--space-1);
        }

        .sp-close-btn:hover {
          color: var(--color-text-primary);
        }

        .sp-hint {
          padding: var(--space-2) var(--space-6);
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
          border-bottom: 1px solid var(--color-border-subtle);
        }

        .sp-message {
          margin: var(--space-2) var(--space-6) 0;
          padding: var(--space-2) var(--space-3);
          background: var(--color-bg-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-size: var(--text-sm);
        }

        .sp-list {
          overflow-y: auto;
          padding: var(--space-3) var(--space-4);
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
          min-height: 120px;
        }

        .sp-empty {
          padding: var(--space-8);
          text-align: center;
          color: var(--color-text-muted);
        }

        .sp-error {
          color: var(--color-danger);
        }

        .sp-row {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border-subtle);
          background: var(--color-bg-surface);
        }

        .sp-row--installed {
          border-color: var(--color-cyan);
        }

        .sp-row--original .sp-pack-name {
          color: var(--color-text-secondary);
        }

        .sp-pack-name {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--color-text-primary);
          font-weight: 600;
          font-size: var(--text-sm);
        }

        .sp-pack-meta {
          flex-shrink: 0;
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
          font-variant-numeric: tabular-nums;
        }

        .sp-actions {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          flex-shrink: 0;
        }

        .sp-action-btn {
          background: transparent;
          border: 1px solid var(--color-border);
          color: var(--color-text-secondary);
          border-radius: var(--radius-md);
          padding: 3px 8px;
          cursor: pointer;
          font-size: var(--text-sm);
        }

        .sp-action-btn:hover:not(:disabled) {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sp-action-btn:disabled {
          opacity: 0.5;
          cursor: default;
        }

        .sp-install-btn {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sp-install-btn:hover:not(:disabled) {
          background: var(--color-cyan-muted);
        }

        .sp-installed-badge {
          color: var(--color-cyan);
          font-size: var(--text-sm);
          padding: 3px 8px;
          white-space: nowrap;
        }

        .sp-delete-btn:hover:not(:disabled) {
          border-color: var(--color-danger);
          color: var(--color-danger);
        }

        .sp-delete-confirm {
          border-color: var(--color-danger);
          color: var(--color-danger);
        }

        .sp-footer {
          padding: var(--space-3) var(--space-4);
          border-top: 1px solid var(--color-border-subtle);
          flex-shrink: 0;
        }

        .sp-new-pack-btn {
          width: 100%;
          background: transparent;
          border: 1px dashed var(--color-border);
          color: var(--color-text-secondary);
          border-radius: var(--radius-md);
          padding: var(--space-2);
          cursor: pointer;
          font-size: var(--text-sm);
        }

        .sp-new-pack-btn:hover:not(:disabled) {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sp-create-row {
          display: flex;
          gap: var(--space-2);
        }

        .sp-name-input {
          flex: 1;
          background: var(--color-bg-deep);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-primary);
          padding: var(--space-1) var(--space-2);
          font-size: var(--text-sm);
        }

        .sp-name-input:focus {
          outline: none;
          border-color: var(--color-cyan);
        }
`
