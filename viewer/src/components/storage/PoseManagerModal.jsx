import { useState, useRef, useEffect, useCallback } from 'react'
import EmbeddedModelViewer from '../EmbeddedModelViewer'

/**
 * Pose Manager Modal
 * Allows users to pose characters and save poses for CSP generation
 * Left side: 3D viewer for posing
 * Right side: Grid of saved poses with thumbnails
 */

// Character to costume code prefix mapping
const CHAR_PREFIXES = {
  "C. Falcon": "PlCa", "Falco": "PlFc", "Fox": "PlFx",
  "Marth": "PlMs", "Roy": "PlFe", "Bowser": "PlKp",
  "DK": "PlDk", "Ganondorf": "PlGn", "Jigglypuff": "PlPr",
  "Kirby": "PlKb", "Link": "PlLk", "Luigi": "PlLg",
  "Mario": "PlMr", "Mewtwo": "PlMt", "Ness": "PlNs",
  "Peach": "PlPe", "Pichu": "PlPc", "Pikachu": "PlPk",
  "Ice Climbers": "PlPp", "Samus": "PlSs", "Sheik": "PlSk",
  "Yoshi": "PlYs", "Young Link": "PlCl", "Zelda": "PlZd",
  "Dr. Mario": "PlDr", "G&W": "PlGw"
}

// Get default costume code for a character (e.g., "PlFxNr" for Fox)
const getDefaultCostumeCode = (character) => {
  const prefix = CHAR_PREFIXES[character]
  return prefix ? `${prefix}Nr` : null
}

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

const SaveIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
    <polyline points="17 21 17 13 7 13 7 21"/>
    <polyline points="7 3 7 8 15 8"/>
  </svg>
)

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
)

// Pose Card Component
function PoseCard({ pose, character, onDelete, API_URL }) {
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
    <div className="pm-pose-card">
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

export default function PoseManagerModal({
  show,
  character,
  onClose,
  API_URL
}) {
  const [poseName, setPoseName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [poses, setPoses] = useState([])
  const [loadingPoses, setLoadingPoses] = useState(true)
  const viewerRef = useRef(null)

  // Fetch saved poses
  const fetchPoses = useCallback(async () => {
    if (!character) return
    try {
      const response = await fetch(`${API_URL}/storage/poses/list/${character}`)
      const data = await response.json()
      if (data.success) {
        setPoses(data.poses)
      }
    } catch (err) {
      console.error('[PoseManager] Fetch poses error:', err)
    } finally {
      setLoadingPoses(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    if (show) {
      fetchPoses()
    }
  }, [show, fetchPoses])

  if (!show) return null

  const handleSavePose = async () => {
    if (!poseName.trim()) {
      setSaveError('Please enter a pose name')
      return
    }

    if (!viewerRef.current) {
      setSaveError('Viewer not ready')
      return
    }

    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Export scene from viewer
      const sceneData = await viewerRef.current.exportScene()
      if (!sceneData) {
        throw new Error('Failed to export scene data')
      }

      // Save pose via API
      const response = await fetch(`${API_URL}/storage/poses/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          poseName: poseName.trim(),
          sceneData
        })
      })

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error || 'Failed to save pose')
      }

      setSaveSuccess(true)
      setPoseName('')

      // Refresh poses list to show new thumbnail
      await fetchPoses()

      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('[PoseManager] Save error:', err)
      setSaveError(err.message || 'Failed to save pose')
    } finally {
      setSaving(false)
    }
  }

  const handleDeletePose = (poseName) => {
    setPoses(poses.filter(p => p.name !== poseName))
  }

  return (
    <div className="pm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="pm-modal">
        {/* Header */}
        <div className="pm-header">
          <div className="pm-title">
            <span className="pm-title-label">Pose Manager</span>
            <span className="pm-title-char">{character}</span>
          </div>
          <button className="pm-close-btn" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        {/* Body with viewer and poses grid */}
        <div className="pm-body">
          {/* Left: 3D Viewer */}
          <div className="pm-viewer-section">
            <EmbeddedModelViewer
              ref={viewerRef}
              character={character}
              costumeCode={getDefaultCostumeCode(character)}
              onClose={onClose}
              cspMode={true}
              showGrid={false}
              showBackground={false}
            />
          </div>

          {/* Right: Saved Poses Grid */}
          <div className="pm-poses-section">
            <div className="pm-poses-header">
              <span>Saved Poses</span>
              <span className="pm-poses-count">{poses.length}</span>
            </div>
            <div className="pm-poses-grid">
              {loadingPoses ? (
                <div className="pm-poses-loading">Loading poses...</div>
              ) : poses.length === 0 ? (
                <div className="pm-poses-empty">
                  No saved poses yet.<br/>
                  Create a pose and save it!
                </div>
              ) : (
                poses.map(pose => (
                  <PoseCard
                    key={pose.name}
                    pose={pose}
                    character={character}
                    onDelete={handleDeletePose}
                    API_URL={API_URL}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Save controls */}
        <div className="pm-save-controls">
          <input
            type="text"
            className="pm-pose-name-input"
            placeholder="Enter pose name..."
            value={poseName}
            onChange={(e) => setPoseName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSavePose()}
            disabled={saving}
          />
          <button
            className="pm-save-btn"
            onClick={handleSavePose}
            disabled={saving || !poseName.trim()}
          >
            <SaveIcon />
            <span>{saving ? 'Saving...' : 'Save Pose'}</span>
          </button>
        </div>

        {/* Status messages */}
        {saveError && (
          <div className="pm-message pm-error">
            {saveError}
          </div>
        )}
        {saveSuccess && (
          <div className="pm-message pm-success">
            Pose saved successfully!
          </div>
        )}
      </div>

      <style>{`
        .pm-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .pm-modal {
          background: #1a1a2e;
          border-radius: 12px;
          width: 95vw;
          max-width: 1600px;
          height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .pm-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: #16162a;
          border-bottom: 1px solid #2a2a4a;
        }

        .pm-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .pm-title-label {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }

        .pm-title-char {
          font-size: 14px;
          color: #888;
          padding: 4px 10px;
          background: #2a2a4a;
          border-radius: 4px;
        }

        .pm-close-btn {
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.15s ease;
        }

        .pm-close-btn:hover {
          background: #2a2a4a;
          color: #fff;
        }

        .pm-body {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        /* Left: Viewer Section */
        .pm-viewer-section {
          flex: 1;
          position: relative;
          overflow: hidden;
          border-right: 1px solid #2a2a4a;
        }

        .pm-viewer-section .mv-overlay {
          position: absolute;
          background: transparent;
        }

        .pm-viewer-section .mv-container {
          width: 100%;
          height: 100%;
          max-width: none;
          max-height: none;
          border-radius: 0;
        }

        .pm-viewer-section .mv-header {
          display: none;
        }

        /* Right: Poses Section */
        .pm-poses-section {
          width: 320px;
          min-width: 280px;
          display: flex;
          flex-direction: column;
          background: #16162a;
        }

        .pm-poses-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #2a2a4a;
          font-size: 14px;
          font-weight: 500;
          color: #fff;
        }

        .pm-poses-count {
          background: #2a2a4a;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
          color: #888;
        }

        .pm-poses-grid {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          align-content: start;
        }

        .pm-poses-loading,
        .pm-poses-empty {
          grid-column: 1 / -1;
          text-align: center;
          color: #666;
          font-size: 13px;
          padding: 40px 20px;
          line-height: 1.6;
        }

        /* Pose Card */
        .pm-pose-card {
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.15s ease;
        }

        .pm-pose-card:hover {
          border-color: #4a9eff;
          transform: translateY(-2px);
        }

        .pm-pose-image {
          position: relative;
          aspect-ratio: 3 / 4;
          background: #0d1929;
          overflow: hidden;
        }

        .pm-pose-image img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .pm-pose-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          font-weight: 600;
          color: #2a2a4a;
          background: linear-gradient(135deg, #1a1a2e 0%, #0d1929 100%);
        }

        .pm-pose-delete {
          position: absolute;
          top: 6px;
          right: 6px;
          background: rgba(220, 53, 69, 0.9);
          border: none;
          border-radius: 4px;
          padding: 6px;
          color: #fff;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.15s ease;
        }

        .pm-pose-card:hover .pm-pose-delete {
          opacity: 1;
        }

        .pm-pose-delete:hover {
          background: #dc3545;
        }

        .pm-pose-name {
          padding: 8px;
          font-size: 12px;
          color: #ccc;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .pm-save-controls {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pm-pose-name-input {
          flex: 1;
          padding: 12px 16px;
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          outline: none;
          transition: border-color 0.15s ease;
        }

        .pm-pose-name-input:focus {
          border-color: #4a9eff;
        }

        .pm-pose-name-input::placeholder {
          color: #666;
        }

        .pm-pose-name-input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-save-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: linear-gradient(135deg, #4a9eff, #3d7ede);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pm-save-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #5aadff, #4d8eee);
          transform: translateY(-1px);
        }

        .pm-save-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-message {
          padding: 12px 20px;
          font-size: 14px;
          text-align: center;
        }

        .pm-error {
          background: rgba(220, 53, 69, 0.2);
          color: #ff6b6b;
          border-top: 1px solid rgba(220, 53, 69, 0.3);
        }

        .pm-success {
          background: rgba(40, 167, 69, 0.2);
          color: #51cf66;
          border-top: 1px solid rgba(40, 167, 69, 0.3);
        }
      `}</style>
    </div>
  )
}
