/**
 * ClearStorageSection - Clear all vault storage functionality
 *
 * Features:
 * - Clear all character costumes and stage variants
 * - Confirmation modal with item counts
 * - Success/error messaging
 * - Page reload after successful clear
 */
import { useState } from 'react'
import { getStorageStats } from './StorageStatsSection'

export default function ClearStorageSection({ metadata, API_URL }) {
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState({ text: '', type: '' })

  const stats = getStorageStats(metadata)

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
        body: JSON.stringify({}),
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
    <>
      {/* Main Section */}
      <section className="settings-section">
        <h3>Clear Storage</h3>
        <p className="section-description">
          Remove all character costumes and stage variants from storage. This action cannot be undone.
        </p>

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
    </>
  )
}
