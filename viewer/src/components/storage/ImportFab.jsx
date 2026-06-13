/**
 * ImportFab - THE import affordance for the whole vault.
 *
 * A floating bottom-right button that is always visible across every storage
 * view, plus a window-wide drag-and-drop overlay. Both feed the unified
 * /import/file pipeline, which auto-detects costumes, stages, custom
 * characters/stages (incl. classic stage.yml packages), bundles, xdelta
 * patches, and menu mods — so this one button replaces the per-view import
 * buttons that used to be scattered around the app.
 */
import { useEffect, useRef, useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

const ACCEPT = '.zip,.7z,.dat,.usd,.xdelta,.ssbm,.iso,.gcm'

export default function ImportFab({ importing, importMessage, onImportFiles }) {
  const [dragActive, setDragActive] = useState(false)
  const dragDepth = useRef(0)

  useEffect(() => {
    // Only react to OS file drags. Two guards: (1) an explicit flag set by
    // internal card drags (reorder / costume-to-skin) — Electron sometimes
    // reports 'Files' in dataTransfer.types even for in-app element drags, so
    // the type check alone isn't enough; (2) the dataTransfer 'Files' type.
    const hasFiles = (e) => {
      if (document.documentElement.dataset.nucInternalDrag === '1') return false
      return Array.from(e.dataTransfer?.types || []).includes('Files')
    }

    const onDragEnter = (e) => {
      if (!hasFiles(e)) return
      e.preventDefault()
      dragDepth.current += 1
      setDragActive(true)
    }
    const onDragOver = (e) => {
      if (!hasFiles(e)) return
      e.preventDefault()
    }
    const onDragLeave = (e) => {
      if (!hasFiles(e)) return
      dragDepth.current -= 1
      if (dragDepth.current <= 0) {
        dragDepth.current = 0
        setDragActive(false)
      }
    }
    const onDrop = (e) => {
      if (!hasFiles(e)) return
      e.preventDefault()
      dragDepth.current = 0
      setDragActive(false)
      const files = Array.from(e.dataTransfer.files || [])
      if (files.length) {
        playSound('start')
        onImportFiles(files)
      }
    }

    window.addEventListener('dragenter', onDragEnter)
    window.addEventListener('dragover', onDragOver)
    window.addEventListener('dragleave', onDragLeave)
    window.addEventListener('drop', onDrop)
    return () => {
      window.removeEventListener('dragenter', onDragEnter)
      window.removeEventListener('dragover', onDragOver)
      window.removeEventListener('dragleave', onDragLeave)
      window.removeEventListener('drop', onDrop)
    }
  }, [onImportFiles])

  const isError = importMessage &&
    (importMessage.includes('✗') || importMessage.includes('failed') || importMessage.includes('Error'))

  return (
    <>
      {dragActive && (
        <div className="import-drop-overlay">
          <div className="import-drop-card">
            <div className="import-drop-title">Drop to import</div>
            <div className="import-drop-subtitle">
              skins · stages · custom characters · patches · bundles · menu mods · ISOs to scan
            </div>
          </div>
        </div>
      )}

      <div className="import-fab-container">
        {importMessage && (
          <div className={`import-fab-toast ${isError ? 'error' : 'success'}`}>
            {importMessage}
          </div>
        )}
        <label
          className={`import-fab ${importing ? 'busy' : ''}`}
          onMouseEnter={playHoverSound}
          onClick={() => { if (!importing) playSound('start') }}
          title="Import anything — skins, stages, custom characters, patches, bundles, menu mods, or ISOs to scan. Or just drop files anywhere."
        >
          <span className="import-fab-icon">{importing ? '⋯' : '+'}</span>
          <span className="import-fab-label">{importing ? 'Importing' : 'Import'}</span>
          <input
            type="file"
            accept={ACCEPT}
            onChange={(e) => {
              const files = Array.from(e.target.files || [])
              e.target.value = null
              if (files.length) onImportFiles(files)
            }}
            disabled={importing}
            multiple
            style={{ display: 'none' }}
          />
        </label>
      </div>
    </>
  )
}
