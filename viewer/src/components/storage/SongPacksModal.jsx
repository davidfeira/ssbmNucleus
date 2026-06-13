import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { getAppContentPortalTarget } from './appContentPortal'
import { CloseIcon } from '../shared/Icons'
import { playSound, playHoverSound } from '../../utils/sounds'
import { toUploadableAudio } from '../../utils/audioConvert'

/**
 * Song pack manager for a DAS stage: a stage can have any number of
 * alternate music playlists (packs) in the vault. Each pack is a list of
 * tracks with play chances, edited inline; packs are installed into a
 * project as an explicit action (installMode) — nothing applies
 * automatically. Uninstalling restores the stage's vanilla music.
 */
export default function SongPacksModal({ show, stage, displayName, API_URL, onClose, installMode = false }) {
  const [packs, setPacks] = useState([])
  const [installed, setInstalled] = useState(null)
  const [projectOpen, setProjectOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)
  // pack being edited (track view); null = pack list view
  const [editingPack, setEditingPack] = useState(null)
  const [tracks, setTracks] = useState([])
  const [playingTrack, setPlayingTrack] = useState(null)
  const audioRef = useRef(null)
  const trackFileRef = useRef(null)
  const messageTimerRef = useRef(null)

  const base = `${API_URL}/das/${encodeURIComponent(stage)}/song-packs`

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
      } else {
        setError(data.error || 'Failed to load song packs')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [base])

  const fetchTracks = useCallback(async (packId) => {
    try {
      const response = await fetch(`${base}/${packId}/tracks`)
      const data = await response.json()
      if (data.success) setTracks(data.tracks)
    } catch (err) {
      console.error('Failed to fetch pack tracks:', err)
    }
  }, [base])

  useEffect(() => {
    if (show) {
      fetchPacks()
    } else {
      audioRef.current?.pause()
      audioRef.current = null
      setPlayingTrack(null)
      setCreating(false)
      setNewName('')
      setConfirmDeleteId(null)
      setEditingPack(null)
      setTracks([])
    }
  }, [show, fetchPacks])

  useEffect(() => () => {
    audioRef.current?.pause()
    clearTimeout(messageTimerRef.current)
  }, [])

  const flashMessage = (text) => {
    setMessage(text)
    clearTimeout(messageTimerRef.current)
    messageTimerRef.current = setTimeout(() => setMessage(''), 4000)
  }

  const openPackEditor = async (pack) => {
    playSound('boop')
    setTracks([])
    setEditingPack(pack)
    await fetchTracks(pack.id)
  }

  const closePackEditor = async () => {
    playSound('back')
    audioRef.current?.pause()
    audioRef.current = null
    setPlayingTrack(null)
    setEditingPack(null)
    await fetchPacks()
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
        // jump straight into adding songs to the new pack
        await openPackEditor({ id: data.id, name: data.name })
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
        flashMessage(`Installed "${pack.name}" — ${data.tracks} song(s) play on this stage in this project`)
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
    flashMessage('Restoring vanilla music…')
    try {
      const response = await fetch(`${base}/uninstall`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        flashMessage('Vanilla music restored in this project')
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

  // ── Track editing (inside a pack) ──

  const toggleTrack = (index) => {
    if (playingTrack === index) {
      audioRef.current?.pause()
      audioRef.current = null
      setPlayingTrack(null)
      return
    }
    audioRef.current?.pause()
    const audio = new Audio(`${base}/${editingPack.id}/track/${index}`)
    audio.onended = () => setPlayingTrack(null)
    audio.onerror = () => setPlayingTrack(null)
    audioRef.current = audio
    audio.play().catch(() => setPlayingTrack(null))
    setPlayingTrack(index)
  }

  const handleAddTrack = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !editingPack) return
    setBusy(true)
    try {
      // mp3/ogg/etc are decoded to WAV in the browser — the backend's audio
      // library only reads native Melee formats
      const upload = await toUploadableAudio(file)
      const formData = new FormData()
      formData.append('file', upload)
      formData.append('name', file.name.replace(/\.[^.]+$/, ''))
      const response = await fetch(`${base}/${editingPack.id}/tracks/add`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        flashMessage(`Added "${data.track.name}"`)
        await fetchTracks(editingPack.id)
      } else {
        flashMessage(`Add failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Add error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  const handleChanceInput = (index, value) => {
    const chance = parseInt(value, 10)
    if (Number.isNaN(chance)) return
    setTracks(prev => prev.map(t => t.index === index ? { ...t, chance } : t))
  }

  const saveTrackChance = async (index, chance) => {
    try {
      const response = await fetch(`${base}/${editingPack.id}/tracks/${index}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chance })
      })
      const data = await response.json()
      if (!data.success) flashMessage(`Save failed: ${data.error}`)
    } catch (err) {
      flashMessage(`Save error: ${err.message}`)
    }
  }

  const handleRemoveTrack = async (index) => {
    playSound('back')
    if (playingTrack != null) {
      audioRef.current?.pause()
      setPlayingTrack(null)
    }
    setBusy(true)
    try {
      const response = await fetch(`${base}/${editingPack.id}/tracks/${index}/remove`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        await fetchTracks(editingPack.id)
      } else {
        flashMessage(`Remove failed: ${data.error}`)
      }
    } catch (err) {
      flashMessage(`Remove error: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  if (!show) return null

  const canInstall = installMode && projectOpen

  const modal = (
    <div className="sgp-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="sgp-modal">
        <div className="sgp-header">
          <div className="sgp-title">
            {editingPack && (
              <button className="sgp-back-btn" onClick={closePackEditor} title="Back to packs">
                ←
              </button>
            )}
            <span className="sgp-title-label">{editingPack ? editingPack.name : 'Song Packs'}</span>
            <span className="sgp-title-stage">{displayName || stage}</span>
          </div>
          <button className="sgp-close-btn" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="sgp-hint">
          {editingPack
            ? 'Songs played on this stage — % sets how often each one is picked. Add MP3s, WAVs… they convert automatically.'
            : canInstall
              ? 'Pick which songs this stage plays in this project — installing applies the pack to this build only.'
              : 'Build alternate music playlists for this stage. Install them per project from the Install tab.'}
        </div>

        {message && <div className="sgp-message">{message}</div>}

        {editingPack ? (
          <div className="sgp-list">
            {tracks.map((track) => (
              <div key={track.index} className="sgp-row">
                <button
                  className={`sgp-play-btn ${playingTrack === track.index ? 'playing' : ''}`}
                  onMouseEnter={playHoverSound}
                  onClick={() => toggleTrack(track.index)}
                  disabled={!track.has_file || busy}
                  title="Preview"
                >
                  {playingTrack === track.index ? '⏸' : '▶'}
                </button>
                <span className="sgp-track-name" title={track.name}>{track.name}</span>
                <span className="sgp-track-ratio">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={track.chance}
                    onChange={(e) => handleChanceInput(track.index, e.target.value)}
                    onBlur={(e) => saveTrackChance(track.index, Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0)))}
                    onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur() }}
                    className="sgp-chance-input"
                    disabled={busy}
                    title="Chance to play (%)"
                  />
                  <span className="sgp-pct">%</span>
                </span>
                <button
                  className="sgp-action-btn sgp-delete-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => handleRemoveTrack(track.index)}
                  disabled={busy}
                  title="Remove this song"
                >
                  ✕
                </button>
              </div>
            ))}
            {tracks.length === 0 && (
              <div className="sgp-empty">No songs yet — add some below.</div>
            )}
            <button
              className="sgp-new-pack-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); trackFileRef.current?.click() }}
              disabled={busy}
              title="Add a song (mp3, wav... converted to Melee's format automatically)"
            >
              {busy ? 'Working…' : '+ Add Song'}
            </button>
            <input
              ref={trackFileRef}
              type="file"
              accept="audio/*,.wav,.mp3,.ogg,.m4a,.flac,.hps,.brstm,.dsp"
              onChange={handleAddTrack}
              style={{ display: 'none' }}
            />
          </div>
        ) : (
          <>
            <div className="sgp-list">
              {loading ? (
                <div className="sgp-empty">Loading song packs…</div>
              ) : error ? (
                <div className="sgp-empty sgp-error">{error}</div>
              ) : (
                <>
                  {canInstall && (
                    <div className={`sgp-row sgp-row--original ${installed == null ? 'sgp-row--installed' : ''}`}>
                      <span className="sgp-pack-name">Vanilla Music</span>
                      <span className="sgp-pack-meta">default song</span>
                      <span className="sgp-actions">
                        {installed == null ? (
                          <span className="sgp-installed-badge">✓ In this project</span>
                        ) : (
                          <button
                            className="sgp-action-btn sgp-install-btn"
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
                      className={`sgp-row ${canInstall && installed === pack.id ? 'sgp-row--installed' : ''}`}
                    >
                      <span className="sgp-pack-name" title={pack.name}>{pack.name}</span>
                      <span className="sgp-pack-meta">
                        {pack.track_count} song{pack.track_count === 1 ? '' : 's'}
                      </span>
                      <span className="sgp-actions">
                        {canInstall && (installed === pack.id ? (
                          <span className="sgp-installed-badge">✓ In this project</span>
                        ) : (
                          <button
                            className="sgp-action-btn sgp-install-btn"
                            onMouseEnter={playHoverSound}
                            onClick={() => handleInstall(pack)}
                            disabled={busy || pack.track_count === 0}
                            title={pack.track_count === 0
                              ? 'Add songs to this pack first'
                              : 'Install this pack into the open project'}
                          >
                            Install
                          </button>
                        ))}
                        <button
                          className="sgp-action-btn"
                          onMouseEnter={playHoverSound}
                          onClick={() => openPackEditor(pack)}
                          disabled={busy}
                          title="Edit this pack's songs"
                        >
                          Edit
                        </button>
                        {confirmDeleteId === pack.id ? (
                          <button
                            className="sgp-action-btn sgp-delete-btn sgp-delete-confirm"
                            onMouseEnter={playHoverSound}
                            onClick={() => handleDelete(pack)}
                            disabled={busy}
                          >
                            Delete?
                          </button>
                        ) : (
                          <button
                            className="sgp-action-btn sgp-delete-btn"
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
                    <div className="sgp-empty">
                      No song packs yet — create one to give
                      {' '}{displayName || stage} an alternate soundtrack.
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="sgp-footer">
              {creating ? (
                <div className="sgp-create-row">
                  <input
                    className="sgp-name-input"
                    autoFocus
                    placeholder="Pack name (e.g. Jazz Mix)"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreate()
                      if (e.key === 'Escape') { setCreating(false); setNewName('') }
                    }}
                    disabled={busy}
                  />
                  <button
                    className="sgp-action-btn sgp-install-btn"
                    onClick={handleCreate}
                    disabled={busy || !newName.trim()}
                  >
                    Create
                  </button>
                  <button
                    className="sgp-action-btn"
                    onClick={() => { playSound('back'); setCreating(false); setNewName('') }}
                    disabled={busy}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  className="sgp-new-pack-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); setCreating(true); }}
                  disabled={busy || loading}
                >
                  + New Song Pack
                </button>
              )}
            </div>
          </>
        )}
      </div>

      <style>{SONG_PACKS_STYLES}</style>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}

const SONG_PACKS_STYLES = `
        .sgp-overlay {
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

        .sgp-modal {
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

        .sgp-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-3) var(--space-6);
          background: rgba(0, 0, 0, 0.15);
          border-bottom: 1px solid var(--color-border-subtle);
          flex-shrink: 0;
        }

        .sgp-title {
          display: flex;
          align-items: baseline;
          gap: var(--space-3);
          min-width: 0;
        }

        .sgp-back-btn {
          background: transparent;
          border: 1px solid var(--color-border);
          color: var(--color-text-secondary);
          border-radius: var(--radius-md);
          padding: 2px 8px;
          cursor: pointer;
        }

        .sgp-back-btn:hover {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sgp-title-label {
          font-size: var(--text-lg);
          font-weight: 700;
          color: var(--color-text-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .sgp-title-stage {
          color: var(--color-cyan);
          font-weight: 600;
          white-space: nowrap;
        }

        .sgp-close-btn {
          background: transparent;
          border: none;
          color: var(--color-text-secondary);
          cursor: pointer;
          display: flex;
          padding: var(--space-1);
        }

        .sgp-close-btn:hover {
          color: var(--color-text-primary);
        }

        .sgp-hint {
          padding: var(--space-2) var(--space-6);
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
          border-bottom: 1px solid var(--color-border-subtle);
        }

        .sgp-message {
          margin: var(--space-2) var(--space-6) 0;
          padding: var(--space-2) var(--space-3);
          background: var(--color-bg-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-size: var(--text-sm);
        }

        .sgp-list {
          overflow-y: auto;
          padding: var(--space-3) var(--space-4);
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
          min-height: 120px;
        }

        .sgp-empty {
          padding: var(--space-8);
          text-align: center;
          color: var(--color-text-muted);
        }

        .sgp-error {
          color: var(--color-danger);
        }

        .sgp-row {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border-subtle);
          background: var(--color-bg-surface);
        }

        .sgp-row--installed {
          border-color: var(--color-cyan);
        }

        .sgp-row--original .sgp-pack-name {
          color: var(--color-text-secondary);
        }

        .sgp-pack-name,
        .sgp-track-name {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--color-text-primary);
          font-weight: 600;
          font-size: var(--text-sm);
        }

        .sgp-track-name {
          font-weight: 400;
        }

        .sgp-pack-meta {
          flex-shrink: 0;
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
          font-variant-numeric: tabular-nums;
        }

        .sgp-actions {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          flex-shrink: 0;
        }

        .sgp-play-btn {
          width: 28px;
          height: 28px;
          flex-shrink: 0;
          border-radius: 50%;
          border: 1px solid var(--color-border);
          background: var(--color-bg-surface);
          color: var(--color-text-primary);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
        }

        .sgp-play-btn:hover:not(:disabled),
        .sgp-play-btn.playing {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sgp-play-btn:disabled {
          opacity: 0.4;
          cursor: default;
        }

        .sgp-track-ratio {
          display: flex;
          align-items: center;
          gap: 2px;
          flex-shrink: 0;
        }

        .sgp-chance-input {
          width: 48px;
          background: var(--color-bg-deep);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-primary);
          padding: 2px 4px;
          font-size: var(--text-sm);
          text-align: right;
        }

        .sgp-chance-input:focus {
          outline: none;
          border-color: var(--color-cyan);
        }

        .sgp-pct {
          color: var(--color-text-tertiary);
          font-size: var(--text-sm);
        }

        .sgp-action-btn {
          background: transparent;
          border: 1px solid var(--color-border);
          color: var(--color-text-secondary);
          border-radius: var(--radius-md);
          padding: 3px 8px;
          cursor: pointer;
          font-size: var(--text-sm);
        }

        .sgp-action-btn:hover:not(:disabled) {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sgp-action-btn:disabled {
          opacity: 0.5;
          cursor: default;
        }

        .sgp-install-btn {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sgp-install-btn:hover:not(:disabled) {
          background: var(--color-cyan-muted);
        }

        .sgp-installed-badge {
          color: var(--color-cyan);
          font-size: var(--text-sm);
          padding: 3px 8px;
          white-space: nowrap;
        }

        .sgp-delete-btn:hover:not(:disabled) {
          border-color: var(--color-danger);
          color: var(--color-danger);
        }

        .sgp-delete-confirm {
          border-color: var(--color-danger);
          color: var(--color-danger);
        }

        .sgp-footer {
          padding: var(--space-3) var(--space-4);
          border-top: 1px solid var(--color-border-subtle);
          flex-shrink: 0;
        }

        .sgp-new-pack-btn {
          width: 100%;
          background: transparent;
          border: 1px dashed var(--color-border);
          color: var(--color-text-secondary);
          border-radius: var(--radius-md);
          padding: var(--space-2);
          cursor: pointer;
          font-size: var(--text-sm);
        }

        .sgp-new-pack-btn:hover:not(:disabled) {
          border-color: var(--color-cyan);
          color: var(--color-cyan);
        }

        .sgp-create-row {
          display: flex;
          gap: var(--space-2);
        }

        .sgp-name-input {
          flex: 1;
          background: var(--color-bg-deep);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-primary);
          padding: var(--space-1) var(--space-2);
          font-size: var(--text-sm);
        }

        .sgp-name-input:focus {
          outline: none;
          border-color: var(--color-cyan);
        }
`
