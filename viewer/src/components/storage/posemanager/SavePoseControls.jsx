import { SaveIcon } from '../../shared/Icons'

// Bottom: pose name input + save button + status messages
export default function SavePoseControls({ poseLibrary }) {
  const {
    poseName,
    setPoseName,
    saving,
    saveError,
    saveSuccess,
    handleSavePose
  } = poseLibrary

  return (
    <>
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
    </>
  )
}
