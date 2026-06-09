import { playSound, playHoverSound } from '../../utils/sounds'
import { BACKEND_URL } from '../../config'

// Costume selection step: pick a vanilla costume as the starting point.
export default function CostumeSelectStep({
  initialCostume,
  onBack,
  vanillaCostumes,
  selectedCharacter,
  loading,
  error,
  reconnecting,
  reconnectAttempts,
  maxReconnectAttempts,
  onSelectCostume
}) {
  return (
    <div className="skin-creator-select">
      {initialCostume ? (
        <div className="skin-creator-loading-edit">
          <div className="loading-spinner"></div>
          <span>Loading skin editor...</span>
        </div>
      ) : (
      <div className="skin-creator-select-content">
        <div className="skin-creator-select-header">
          <button
            className="back-button"
            onClick={onBack}
          >
            ← Back
          </button>
        </div>
        <h2>Select a base costume</h2>
        <p>Choose a vanilla costume to use as your starting point</p>

      {loading && (
        <div className="skin-creator-loading">Loading costumes...</div>
      )}

      {reconnecting && (
        <div className="skin-creator-reconnecting">
          Reconnecting... (attempt {reconnectAttempts}/{maxReconnectAttempts})
        </div>
      )}

      {error && error !== 'closing' && (
        <div className="skin-creator-error">{error}</div>
      )}

      <div className="skin-creator-costume-grid">
        {vanillaCostumes.map(costume => (
          <div
            key={costume.code}
            className="skin-creator-costume-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); onSelectCostume(costume); }}
          >
            <div className="costume-preview">
              {costume.hasCsp ? (
                <img
                  src={`${BACKEND_URL}/vanilla/${selectedCharacter}/${costume.code}/csp.png`}
                  alt={costume.colorName}
                />
              ) : (
                <div className="costume-placeholder">{costume.colorCode}</div>
              )}
            </div>
            <div className="costume-name">{costume.colorName}</div>
          </div>
        ))}
      </div>
      </div>
      )}
    </div>
  )
}
