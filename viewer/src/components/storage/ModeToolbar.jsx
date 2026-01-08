/**
 * ModeToolbar - Mode switcher for Characters/Stages/Patches
 *
 * Features:
 * - Three mode buttons (Characters, Stages, Patches)
 * - Active mode highlighting
 * - Clears selections when switching modes
 */
export default function ModeToolbar({ mode, onModeChange }) {
  return (
    <div className="mode-switcher">
      <button
        className={`mode-btn ${mode === 'characters' ? 'active' : ''}`}
        onClick={() => onModeChange('characters')}
      >
        Characters
      </button>
      <button
        className={`mode-btn ${mode === 'stages' ? 'active' : ''}`}
        onClick={() => onModeChange('stages')}
      >
        Stages
      </button>
      <button
        className={`mode-btn ${mode === 'patches' ? 'active' : ''}`}
        onClick={() => onModeChange('patches')}
      >
        Patches
      </button>
    </div>
  )
}
