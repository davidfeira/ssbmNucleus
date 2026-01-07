/**
 * BackupRestore - Vault backup and restore functionality
 *
 * Features:
 * - Export vault as backup (downloads .zip)
 * - Import vault from backup
 * - Replace or merge modes for restore
 * - Progress/error messages
 */
import { useState } from 'react'

export default function BackupRestore({ API_URL }) {
  // State
  const [backingUp, setBackingUp] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [showRestoreModal, setShowRestoreModal] = useState(false)
  const [restoreFile, setRestoreFile] = useState(null)
  const [restoreMode, setRestoreMode] = useState('replace') // 'replace' or 'merge'
  const [backupMessage, setBackupMessage] = useState({ text: '', type: '' })

  // Handlers
  const handleBackupVault = async () => {
    setBackingUp(true)
    setBackupMessage({ text: 'Creating backup...', type: '' })

    try {
      const response = await fetch(`${API_URL}/storage/backup`, {
        method: 'POST',
      })

      const data = await response.json()

      if (data.success) {
        setBackupMessage({ text: 'Backup created! Downloading...', type: 'success' })

        // Download the backup file
        const downloadUrl = `${API_URL}/storage/backup/download/${data.filename}`
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = data.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        setTimeout(() => {
          setBackupMessage({ text: '', type: '' })
        }, 3000)
      } else {
        setBackupMessage({ text: `Backup failed: ${data.error}`, type: 'error' })
      }
    } catch (err) {
      setBackupMessage({ text: `Error: ${err.message}`, type: 'error' })
    } finally {
      setBackingUp(false)
    }
  }

  const handleRestoreClick = () => {
    setShowRestoreModal(true)
  }

  const handleRestoreFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setRestoreFile(file)
    }
  }

  const confirmRestore = async () => {
    if (!restoreFile) return

    setShowRestoreModal(false)
    setRestoring(true)
    setBackupMessage({ text: 'Restoring vault...', type: '' })

    try {
      const formData = new FormData()
      formData.append('file', restoreFile)
      formData.append('mode', restoreMode)

      const response = await fetch(`${API_URL}/storage/restore`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setBackupMessage({ text: 'Vault restored successfully!', type: 'success' })
        // Reload page after 1.5 seconds to refresh metadata
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } else {
        setBackupMessage({ text: `Restore failed: ${data.error}`, type: 'error' })
        setRestoring(false)
      }
    } catch (err) {
      setBackupMessage({ text: `Error: ${err.message}`, type: 'error' })
      setRestoring(false)
    }
  }

  const cancelRestore = () => {
    setShowRestoreModal(false)
    setRestoreFile(null)
    setRestoreMode('replace')
  }

  return (
    <>
      {/* Main Section */}
      <section className="settings-section">
        <h3>Vault Backup & Restore</h3>
        <p className="section-description">
          Create a backup of your entire vault collection or restore from a previous backup.
        </p>

        <div className="backup-buttons">
          <button
            className="backup-button"
            onClick={handleBackupVault}
            disabled={backingUp || restoring}
          >
            {backingUp ? 'Creating Backup...' : 'Export Vault'}
          </button>

          <button
            className="restore-button"
            onClick={handleRestoreClick}
            disabled={backingUp || restoring}
          >
            {restoring ? 'Restoring...' : 'Import Vault'}
          </button>
        </div>

        {backupMessage.text && (
          <div className={`message ${backupMessage.type}`}>
            {backupMessage.text}
          </div>
        )}
      </section>

      {/* Restore Modal */}
      {showRestoreModal && (
        <div className="modal-overlay" onClick={cancelRestore}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Restore Vault from Backup</h3>
            <p>
              Select a backup file to restore your vault collection.
            </p>

            <div className="file-input-container">
              <label htmlFor="restore-file-input" className="file-input-label">
                {restoreFile ? restoreFile.name : 'Choose backup file...'}
              </label>
              <input
                id="restore-file-input"
                type="file"
                accept=".zip"
                onChange={handleRestoreFileSelect}
                style={{ display: 'none' }}
              />
            </div>

            <div className="restore-mode-options">
              <label className="radio-label">
                <input
                  type="radio"
                  value="replace"
                  checked={restoreMode === 'replace'}
                  onChange={(e) => setRestoreMode(e.target.value)}
                />
                <div>
                  <strong>Replace All</strong>
                  <p className="radio-description">Delete current vault and restore from backup</p>
                </div>
              </label>

              <label className="radio-label">
                <input
                  type="radio"
                  value="merge"
                  checked={restoreMode === 'merge'}
                  onChange={(e) => setRestoreMode(e.target.value)}
                />
                <div>
                  <strong>Merge</strong>
                  <p className="radio-description">Keep current items and add backup items</p>
                </div>
              </label>
            </div>

            {restoreMode === 'replace' && (
              <p className="warning-text">
                Warning: This will delete all current vault items!
              </p>
            )}

            <div className="modal-actions">
              <button className="btn-cancel" onClick={cancelRestore}>
                Cancel
              </button>
              <button
                className="btn-confirm"
                onClick={confirmRestore}
                disabled={!restoreFile}
              >
                Restore Vault
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
