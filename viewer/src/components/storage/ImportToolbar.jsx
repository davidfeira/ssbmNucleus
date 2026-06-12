/**
 * ImportToolbar - mode-specific flows the unified Import button (the floating
 * ImportFab) doesn't cover. Currently just the metadata-rich xdelta/bundle
 * import modal in patches mode. Plain file imports of ANY kind — including
 * ISOs to scan — go through the ImportFab / drag-and-drop.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

export default function ImportToolbar({
  mode,
  onShowXdeltaImportModal
}) {
  if (mode !== 'patches') return null
  return (
    <div className="import-file-container">
      <button
        className="intake-import-btn"
        onMouseEnter={playHoverSound}
        onClick={() => { playSound('start'); onShowXdeltaImportModal(); }}
      >
        Import Patch
      </button>
    </div>
  )
}
