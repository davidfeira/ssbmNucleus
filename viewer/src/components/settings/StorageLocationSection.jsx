/**
 * StorageLocationSection - Custom vault storage location
 *
 * Features:
 * - Display current vault path
 * - Browse for a new path via native folder picker
 * - Save the new path (takes effect on restart)
 * - Move all vault files to the new location
 */
import { useState, useEffect } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function StorageLocationSection({ API_URL }) {
  const [currentPath, setCurrentPath] = useState('')
  const [pendingPath, setPendingPath] = useState(null)
  const [selectedPath, setSelectedPath] = useState('')
  const [message, setMessage] = useState({ text: '', type: '' })
  const [moving, setMoving] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/settings`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setCurrentPath(data.storage_path)
          if (data.pending_storage_path) {
            setPendingPath(data.pending_storage_path)
          }
        }
      })
      .catch(err => console.error('Failed to fetch settings:', err))
  }, [])

  const handleBrowse = async () => {
    if (!window.electron) {
      setMessage({ text: 'Electron API not available', type: 'error' })
      return
    }
    try {
      const dir = await window.electron.selectDirectory()
      if (dir) {
        setSelectedPath(dir)
        setMessage({ text: '', type: '' })
      }
    } catch (err) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' })
    }
  }

  const handleChange = async () => {
    if (!selectedPath) return
    setSaving(true)
    try {
      const res = await fetch(`${API_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storage_path: selectedPath }),
      })
      const data = await res.json()
      if (data.success) {
        setPendingPath(selectedPath)
        setMessage({ text: 'Path saved. Restart the app to apply.', type: 'success' })
      } else {
        setMessage({ text: data.error || 'Failed to save path', type: 'error' })
      }
    } catch (err) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const handleMove = async () => {
    if (!selectedPath) return
    setMoving(true)
    setMessage({ text: 'Copying vault files…', type: '' })
    try {
      const res = await fetch(`${API_URL}/settings/move-storage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storage_path: selectedPath }),
      })
      const data = await res.json()
      if (data.success) {
        setPendingPath(selectedPath)
        setMessage({
          text: `Copied ${data.files_copied} file(s). Restart the app to apply.`,
          type: 'success',
        })
      } else {
        setMessage({ text: data.error || 'Move failed', type: 'error' })
      }
    } catch (err) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' })
    } finally {
      setMoving(false)
    }
  }

  const hasNewPath = selectedPath && selectedPath !== currentPath

  return (
    <section className="settings-section">
      <h3>Vault Location</h3>
      <p className="section-description">
        Choose where the mod vault is stored. Changes take effect on restart.
      </p>

      <div className="iso-path-container">
        <div className="iso-path-display">
          <span className="iso-path-text" title={currentPath}>{currentPath || 'Unknown'}</span>
        </div>
        <button
          className="iso-browse-button"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); handleBrowse() }}
          disabled={moving}
        >
          Browse
        </button>
      </div>

      {hasNewPath && (
        <div className="storage-location-new-path">
          <div className="iso-path-display">
            <span className="iso-path-text" title={selectedPath}>{selectedPath}</span>
          </div>
          <div className="storage-location-actions">
            <button
              className="iso-browse-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); handleChange() }}
              disabled={saving || moving}
              title="Save path without copying files"
            >
              {saving ? 'Saving…' : 'Change'}
            </button>
            <button
              className="iso-browse-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); handleMove() }}
              disabled={saving || moving}
              title="Copy all vault files to the new location"
            >
              {moving ? 'Copying…' : 'Move Vault Files Here'}
            </button>
          </div>
        </div>
      )}

      {pendingPath && (
        <div className="message warning">
          ⚠ Restart required — new path: {pendingPath}
        </div>
      )}

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}
    </section>
  )
}
