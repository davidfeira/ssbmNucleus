import { playSound, playHoverSound } from '../../utils/sounds'
import { BACKEND_URL } from '../../config'

// Costume selection step: pick a vanilla costume as the starting point —
// or hand the whole job to the AI Skin Studio (rendered as one more option).
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
  onSelectCostume,
  aiStudioEnabled,
  aiReady,
  onOpenAiStudio,
  modelStudioEnabled,
  onOpenModelStudio
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
        <p>Choose a starting point</p>

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
        {aiStudioEnabled && (
          <div
            className={`skin-creator-costume-card skin-creator-ai-card${aiReady ? '' : ' gated'}`}
            title={aiReady ? 'Describe a theme and let the AI Studio build the skin'
              : 'Set up AI Studio in Settings (OpenRouter key or a local model)'}
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); onOpenAiStudio(); }}
          >
            <div className="costume-preview">
              <div className="costume-placeholder">{aiReady ? '✨' : '🔒'}</div>
            </div>
            <div className="costume-name">AI Skin Studio</div>
          </div>
        )}
        {modelStudioEnabled && (
          <div
            className="skin-creator-costume-card skin-creator-ai-card"
            title="Generate or upload a 3D model and rig it onto this character's skeleton"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); onOpenModelStudio(); }}
          >
            <div className="costume-preview">
              <div className="costume-placeholder">🎨</div>
            </div>
            <div className="costume-name">AI Model Studio</div>
          </div>
        )}
      </div>
      </div>
      )}
    </div>
  )
}
