import { useState, useRef } from 'react'
import EmbeddedModelViewer from '../EmbeddedModelViewer'

/**
 * Pose Manager Modal
 * Allows users to pose characters and save poses for CSP generation
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
  const viewerRef = useRef(null)

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

      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('[PoseManager] Save error:', err)
      setSaveError(err.message || 'Failed to save pose')
    } finally {
      setSaving(false)
    }
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

        {/* Body with viewer */}
        <div className="pm-body">
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
          max-width: 1400px;
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
          position: relative;
          overflow: hidden;
        }

        .pm-body .mv-overlay {
          position: absolute;
          background: transparent;
        }

        .pm-body .mv-container {
          width: 100%;
          height: 100%;
          max-width: none;
          max-height: none;
          border-radius: 0;
        }

        .pm-body .mv-header {
          display: none;
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
