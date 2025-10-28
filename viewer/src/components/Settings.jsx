import { useState, useEffect } from 'react'
import './Settings.css'

const API_URL = 'http://127.0.0.1:5000/api/mex'

export default function Settings({ metadata }) {
  const [clearIntake, setClearIntake] = useState(false)
  const [clearLogs, setClearLogs] = useState(false)
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState({ text: '', type: '' }) // type: 'success' | 'error'

  // Calculate storage statistics
  const getStorageStats = () => {
    if (!metadata) return { characterCount: 0, stageCount: 0, costumeCount: 0 }

    const characterCount = Object.keys(metadata.characters || {}).length
    let costumeCount = 0

    Object.values(metadata.characters || {}).forEach(char => {
      costumeCount += (char.skins || []).length
    })

    let stageCount = 0
    Object.values(metadata.stages || {}).forEach(stage => {
      stageCount += (stage.variants || []).length
    })

    return { characterCount, stageCount, costumeCount }
  }

  const stats = getStorageStats()

  const handleClearStorage = () => {
    setShowConfirmModal(true)
  }

  const confirmClear = async () => {
    setShowConfirmModal(false)
    setClearing(true)
    setMessage({ text: 'Clearing storage...', type: '' })

    try {
      const response = await fetch(`${API_URL}/storage/clear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clearIntake,
          clearLogs,
        }),
      })

      const data = await response.json()

      if (data.success) {
        setMessage({ text: 'Storage cleared successfully!', type: 'success' })
        // Reload page after 1.5 seconds to refresh metadata
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } else {
        setMessage({ text: `Failed to clear storage: ${data.error}`, type: 'error' })
        setClearing(false)
      }
    } catch (err) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' })
      setClearing(false)
    }
  }

  const cancelClear = () => {
    setShowConfirmModal(false)
  }

  return (
    <div className="settings-container">
      <div className="settings-content">
        <h2>Settings</h2>

        {/* Storage Statistics */}
        <section className="settings-section">
          <h3>Storage Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{stats.characterCount}</div>
              <div className="stat-label">Characters</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.costumeCount}</div>
              <div className="stat-label">Costumes</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.stageCount}</div>
              <div className="stat-label">Stage Variants</div>
            </div>
          </div>
        </section>

        {/* Clear Storage Section */}
        <section className="settings-section">
          <h3>Clear Storage</h3>
          <p className="section-description">
            Remove all character costumes and stage variants from storage. This action cannot be undone.
          </p>

          <div className="options-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={clearIntake}
                onChange={(e) => setClearIntake(e.target.checked)}
                disabled={clearing}
              />
              <span>Also clear intake folder (staged imports)</span>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={clearLogs}
                onChange={(e) => setClearLogs(e.target.checked)}
                disabled={clearing}
              />
              <span>Also clear log files</span>
            </label>
          </div>

          <button
            className="clear-button"
            onClick={handleClearStorage}
            disabled={clearing}
          >
            {clearing ? 'Clearing...' : 'Clear Storage'}
          </button>

          {message.text && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}
        </section>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={cancelClear}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Clear Storage</h3>
            <p>
              Are you sure you want to clear all storage? This will remove:
            </p>
            <ul>
              <li>All character costumes ({stats.costumeCount} items)</li>
              <li>All stage variants ({stats.stageCount} items)</li>
              <li>Storage metadata</li>
              {clearIntake && <li>Intake folder (staged imports)</li>}
              {clearLogs && <li>Log files</li>}
            </ul>
            <p className="warning-text">
              This action cannot be undone!
            </p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={cancelClear}>
                Cancel
              </button>
              <button className="btn-confirm" onClick={confirmClear}>
                Clear Storage
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
