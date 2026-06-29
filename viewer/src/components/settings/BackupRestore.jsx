/**
 * BackupRestore - Vault backup and restore functionality
 *
 * Features:
 * - Export vault as backup (downloads .zip)
 * - Import vault from backup
 * - Replace or merge modes for restore
 * - Live restore progress: upload % (XHR) then extract/merge % (socketio)
 */
import { useState, useEffect, useRef } from 'react'
import { io } from 'socket.io-client'
import { BACKEND_URL } from '../../config'
import ProgressPanel from '../export/ProgressPanel'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function BackupRestore({ API_URL }) {
  // State
  const [backingUp, setBackingUp] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [showRestoreModal, setShowRestoreModal] = useState(false)
  const [restoreFile, setRestoreFile] = useState(null)
  const [restoreMode, setRestoreMode] = useState('replace') // 'replace' or 'merge'
  const [backupMessage, setBackupMessage] = useState({ text: '', type: '' })

  // Live restore progress
  const [restoreProgress, setRestoreProgress] = useState(0)
  const [restoreTitle, setRestoreTitle] = useState('Restoring vault…')
  const [restoreStatus, setRestoreStatus] = useState('')
  const [restoreReport, setRestoreReport] = useState(null) // merge result, shown after finish
  const restoreIdRef = useRef(null)

  // Subscribe to restore progress events (the slow extract/merge runs server-side
  // in a background thread and streams progress over the socket).
  useEffect(() => {
    const socket = io(BACKEND_URL)

    socket.on('vault_restore_progress', (data) => {
      if (data.restore_id !== restoreIdRef.current) return
      setRestoreTitle(restoreMode === 'merge' ? 'Merging vault…' : 'Restoring vault…')
      if (typeof data.percentage === 'number') setRestoreProgress(data.percentage)
      if (data.message) setRestoreStatus(data.message)
    })

    socket.on('vault_restore_complete', (data) => {
      if (data.restore_id !== restoreIdRef.current) return
      restoreIdRef.current = null
      setRestoreProgress(100)
      setRestoreStatus(data.message || 'Done!')
      playSound('start')
      if (data.report) {
        // Merge: show what was added vs. kept; user dismisses to reload.
        setRestoreReport(data.report)
      } else {
        // Replace: nothing to review, just refresh.
        setTimeout(() => window.location.reload(), 1500)
      }
    })

    socket.on('vault_restore_error', (data) => {
      if (data.restore_id !== restoreIdRef.current) return
      restoreIdRef.current = null
      setRestoring(false)
      setBackupMessage({ text: `Restore failed: ${data.error}`, type: 'error' })
    })

    return () => socket.disconnect()
  }, [restoreMode])

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
        playSound('start')

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
      playSound('start')
      setRestoreFile(file)
    }
  }

  const confirmRestore = () => {
    if (!restoreFile) return

    setShowRestoreModal(false)
    setRestoring(true)
    setBackupMessage({ text: '', type: '' })
    setRestoreProgress(0)
    setRestoreTitle('Uploading backup…')
    setRestoreStatus('Sending backup to the app…')
    restoreIdRef.current = null

    const formData = new FormData()
    formData.append('file', restoreFile)
    formData.append('mode', restoreMode)

    // Use XHR (not fetch) so we can show real upload progress for a multi-GB
    // backup; once uploaded, the server returns a restore_id and the socket
    // events drive the extract/merge portion of the bar.
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_URL}/storage/restore`)

    xhr.upload.onprogress = (e) => {
      if (!e.lengthComputable) return
      const pct = Math.round((e.loaded / e.total) * 100)
      setRestoreProgress(pct)
      setRestoreStatus(`Uploading backup… ${pct}%`)
    }

    xhr.onload = () => {
      let data = {}
      try { data = JSON.parse(xhr.responseText) } catch { /* ignore */ }
      if (xhr.status === 200 && data.success && data.restore_id) {
        // Hand off to the socket-driven processing phase.
        restoreIdRef.current = data.restore_id
        setRestoreProgress(0)
        setRestoreTitle(restoreMode === 'merge' ? 'Merging vault…' : 'Restoring vault…')
        setRestoreStatus('Backup received — processing…')
      } else {
        setRestoring(false)
        setBackupMessage({ text: `Restore failed: ${data.error || `HTTP ${xhr.status}`}`, type: 'error' })
      }
    }

    xhr.onerror = () => {
      setRestoring(false)
      setBackupMessage({ text: 'Error: upload failed', type: 'error' })
    }

    xhr.send(formData)
  }

  const cancelRestore = () => {
    setShowRestoreModal(false)
    setRestoreFile(null)
    setRestoreMode('replace')
  }

  // Render one side of the merge report (added / kept): named custom
  // characters/stages, then a count line for the bulkier item types.
  const renderReportSide = (title, side, kind) => {
    if (!side) return null
    const named = [...(side.custom_characters || []), ...(side.custom_stages || [])]
    const counts = []
    if (side.skins?.length) counts.push(`${side.skins.length} skin${side.skins.length === 1 ? '' : 's'}`)
    if (side.variants?.length) counts.push(`${side.variants.length} stage variant${side.variants.length === 1 ? '' : 's'}`)
    if (side.xdelta?.length) counts.push(`${side.xdelta.length} patch${side.xdelta.length === 1 ? '' : 'es'}`)
    if (side.bundles?.length) counts.push(`${side.bundles.length} bundle${side.bundles.length === 1 ? '' : 's'}`)
    const total = named.length + (side.skins?.length || 0) + (side.variants?.length || 0) +
      (side.xdelta?.length || 0) + (side.bundles?.length || 0)
    if (total === 0) {
      return (
        <div className={`report-side report-${kind}`}>
          <strong>{title} (0)</strong>
          <p className="report-empty">{kind === 'kept' ? 'No conflicts.' : 'Nothing new.'}</p>
        </div>
      )
    }
    return (
      <div className={`report-side report-${kind}`}>
        <strong>{title} ({total})</strong>
        {named.length > 0 && (
          <ul className="report-names">
            {named.map((n) => <li key={n}>{n}</li>)}
          </ul>
        )}
        {counts.length > 0 && <p className="report-counts">{counts.join(' · ')}</p>}
      </div>
    )
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
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); handleBackupVault(); }}
            disabled={backingUp || restoring}
          >
            {backingUp ? 'Creating Backup...' : 'Export Vault'}
          </button>

          <button
            className="restore-button"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); handleRestoreClick(); }}
            disabled={backingUp || restoring}
          >
            {restoring ? 'Restoring...' : 'Import Vault'}
          </button>
        </div>

        {restoring && !restoreReport && (
          <ProgressPanel
            title={restoreTitle}
            label="Restore progress"
            progressValue={restoreProgress}
            messageText={restoreStatus || 'Working…'}
          />
        )}

        {restoreReport && (
          <div className="restore-report">
            <h4>{restoreStatus || 'Merge complete'}</h4>
            {renderReportSide('Added to your vault', restoreReport.added, 'added')}
            {renderReportSide('Kept your version (skipped backup’s)', restoreReport.kept, 'kept')}
            <button
              className="backup-button"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('start'); window.location.reload(); }}
            >
              Done
            </button>
          </div>
        )}

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
              <button className="btn-cancel" onMouseEnter={playHoverSound} onClick={() => { playSound('back'); cancelRestore(); }}>
                Cancel
              </button>
              <button
                className="btn-confirm"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); confirmRestore(); }}
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
