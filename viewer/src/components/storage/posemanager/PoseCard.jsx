import { useState } from 'react'
import { TrashIcon } from '../../shared/Icons'

// Pose Card Component
export default function PoseCard({ pose, character, onDelete, onClick, API_URL }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm(`Delete pose "${pose.name}"?`)) return

    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/storage/poses/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character, poseName: pose.name })
      })
      const data = await response.json()
      if (data.success) {
        onDelete(pose.name)
      }
    } catch (err) {
      console.error('[PoseCard] Delete error:', err)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="pm-pose-card" onClick={onClick} style={{ cursor: 'pointer' }}>
      <div className="pm-pose-image">
        {pose.hasThumbnail ? (
          <img
            src={`${API_URL.replace('/api/mex', '')}${pose.thumbnailUrl}`}
            alt={pose.name}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <div className="pm-pose-placeholder">
            {pose.name.charAt(0).toUpperCase()}
          </div>
        )}
        <button
          className="pm-pose-delete"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete pose"
        >
          <TrashIcon />
        </button>
      </div>
      <div className="pm-pose-name">{pose.name}</div>
    </div>
  )
}
