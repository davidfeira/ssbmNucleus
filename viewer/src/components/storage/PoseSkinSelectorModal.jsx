import { useState, useEffect, useCallback } from 'react'

/**
 * Pose Skin Selector Modal
 * Opens when clicking a saved pose, allows selecting multiple skins
 * to batch generate CSPs using that pose
 */

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const GenerateIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
)

// Skin Card with checkbox
function SkinCheckboxCard({ skin, selected, onToggle, API_URL }) {
  return (
    <div
      className={`pss-skin-card ${selected ? 'pss-selected' : ''}`}
      onClick={() => onToggle(skin.folder)}
    >
      <div className="pss-checkbox">
        {selected && <CheckIcon />}
      </div>
      <div className="pss-skin-image">
        {skin.cspUrl ? (
          <img
            src={`${API_URL.replace('/api/mex', '')}${skin.cspUrl}`}
            alt={skin.name}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <div className="pss-skin-placeholder">?</div>
        )}
      </div>
      <div className="pss-skin-name">{skin.name?.split(' - ')[1] || skin.costumeCode}</div>
    </div>
  )
}

export default function PoseSkinSelectorModal({
  show,
  character,
  poseName,
  poseThumbnail,
  onClose,
  onRefresh,
  API_URL
}) {
  const [skins, setSkins] = useState([])
  const [selectedSkins, setSelectedSkins] = useState(new Set())
  const [hdResolution, setHdResolution] = useState('1x')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0, currentSkin: '' })
  const [results, setResults] = useState(null)

  // Fetch skins for this character
  const fetchSkins = useCallback(async () => {
    if (!character) return
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/storage/costumes?character=${encodeURIComponent(character)}`)
      const data = await response.json()
      if (data.success) {
        // Filter to only this character's skins
        const characterSkins = data.costumes.filter(c => c.character === character)
        setSkins(characterSkins)
      }
    } catch (err) {
      console.error('[PoseSkinSelector] Fetch skins error:', err)
    } finally {
      setLoading(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    if (show) {
      fetchSkins()
      setSelectedSkins(new Set())
      setResults(null)
    }
  }, [show, fetchSkins])

  if (!show) return null

  const toggleSkin = (skinId) => {
    setSelectedSkins(prev => {
      const next = new Set(prev)
      if (next.has(skinId)) {
        next.delete(skinId)
      } else {
        next.add(skinId)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelectedSkins(new Set(skins.map(s => s.folder)))
  }

  const deselectAll = () => {
    setSelectedSkins(new Set())
  }

  const handleGenerate = async () => {
    if (selectedSkins.size === 0) return

    setGenerating(true)
    setProgress({ current: 0, total: selectedSkins.size, currentSkin: '' })
    setResults(null)

    try {
      const response = await fetch(`${API_URL}/storage/poses/batch-generate-csp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          poseName,
          skinIds: Array.from(selectedSkins),
          hdResolution: hdResolution !== '1x' ? hdResolution : null
        })
      })

      const data = await response.json()

      if (data.success) {
        setResults({
          generated: data.generated,
          failed: data.failed,
          details: data.results
        })
        // Refresh parent metadata so new CSPs show up
        if (onRefresh) {
          onRefresh()
        }
      } else {
        setResults({
          error: data.error || 'Generation failed'
        })
      }
    } catch (err) {
      console.error('[PoseSkinSelector] Generate error:', err)
      setResults({
        error: err.message || 'Network error'
      })
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="pss-overlay" onClick={(e) => e.target === e.currentTarget && !generating && onClose()}>
      <div className="pss-modal">
        {/* Header */}
        <div className="pss-header">
          <div className="pss-title">
            <span className="pss-title-label">Generate CSPs</span>
            <span className="pss-title-pose">"{poseName}"</span>
          </div>
          <button className="pss-close-btn" onClick={onClose} disabled={generating}>
            <CloseIcon />
          </button>
        </div>

        {/* Pose Preview */}
        {poseThumbnail && (
          <div className="pss-pose-preview">
            <img src={poseThumbnail} alt={poseName} />
            <span>Using this pose for all selected skins</span>
          </div>
        )}

        {/* Controls */}
        <div className="pss-controls">
          <div className="pss-select-btns">
            <button onClick={selectAll} disabled={generating}>Select All</button>
            <button onClick={deselectAll} disabled={generating}>Deselect All</button>
          </div>
          <div className="pss-resolution-picker">
            <span>Resolution:</span>
            <div className="pss-resolution-btns">
              {['1x', '2x', '3x', '4x'].map(res => (
                <button
                  key={res}
                  className={hdResolution === res ? 'active' : ''}
                  onClick={() => setHdResolution(res)}
                  disabled={generating}
                >
                  {res}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Skins Grid */}
        <div className="pss-skins-grid">
          {loading ? (
            <div className="pss-loading">Loading skins...</div>
          ) : skins.length === 0 ? (
            <div className="pss-empty">No skins found for {character}</div>
          ) : (
            skins.map(skin => (
              <SkinCheckboxCard
                key={skin.folder}
                skin={skin}
                selected={selectedSkins.has(skin.folder)}
                onToggle={toggleSkin}
                API_URL={API_URL}
              />
            ))
          )}
        </div>

        {/* Generate Button / Progress */}
        <div className="pss-footer">
          {generating ? (
            <div className="pss-progress">
              <div className="pss-progress-bar">
                <div
                  className="pss-progress-fill"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                />
              </div>
              <span>Generating CSPs... {progress.current}/{progress.total}</span>
            </div>
          ) : results ? (
            <div className={`pss-results ${results.error ? 'pss-error' : 'pss-success'}`}>
              {results.error ? (
                <span>Error: {results.error}</span>
              ) : (
                <span>Generated {results.generated} CSP{results.generated !== 1 ? 's' : ''}{results.failed > 0 ? `, ${results.failed} failed` : ''}</span>
              )}
              <button onClick={onClose}>Done</button>
            </div>
          ) : (
            <button
              className="pss-generate-btn"
              onClick={handleGenerate}
              disabled={selectedSkins.size === 0}
            >
              <GenerateIcon />
              <span>Generate {selectedSkins.size} CSP{selectedSkins.size !== 1 ? 's' : ''}{hdResolution !== '1x' ? ` (${hdResolution})` : ''}</span>
            </button>
          )}
        </div>
      </div>

      <style>{`
        .pss-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.85);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1100;
        }

        .pss-modal {
          background: #1a1a2e;
          border-radius: 12px;
          width: 90vw;
          max-width: 900px;
          max-height: 85vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .pss-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: #16162a;
          border-bottom: 1px solid #2a2a4a;
        }

        .pss-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .pss-title-label {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }

        .pss-title-pose {
          font-size: 14px;
          color: #6c8cff;
          padding: 4px 10px;
          background: rgba(108, 140, 255, 0.15);
          border-radius: 4px;
        }

        .pss-close-btn {
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.15s ease;
        }

        .pss-close-btn:hover:not(:disabled) {
          background: #2a2a4a;
          color: #fff;
        }

        .pss-close-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pss-pose-preview {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px 20px;
          background: #16162a;
          border-bottom: 1px solid #2a2a4a;
        }

        .pss-pose-preview img {
          width: 60px;
          height: 80px;
          object-fit: contain;
          border-radius: 4px;
          background: #0d0d1a;
        }

        .pss-pose-preview span {
          color: #888;
          font-size: 13px;
        }

        .pss-controls {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 20px;
          border-bottom: 1px solid #2a2a4a;
        }

        .pss-select-btns {
          display: flex;
          gap: 8px;
        }

        .pss-select-btns button {
          padding: 6px 12px;
          background: #2a2a4a;
          border: none;
          border-radius: 4px;
          color: #ccc;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.15s ease;
        }

        .pss-select-btns button:hover:not(:disabled) {
          background: #3a3a5a;
          color: #fff;
        }

        .pss-select-btns button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pss-resolution-picker {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #ccc;
          font-size: 13px;
        }

        .pss-resolution-btns {
          display: flex;
          gap: 4px;
        }

        .pss-resolution-btns button {
          padding: 5px 10px;
          background: #2a2a4a;
          border: 1px solid #3a3a5a;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.15s ease;
        }

        .pss-resolution-btns button:hover:not(:disabled) {
          background: #3a3a5a;
          color: #ccc;
        }

        .pss-resolution-btns button.active {
          background: #6c8cff;
          border-color: #6c8cff;
          color: #fff;
        }

        .pss-resolution-btns button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pss-skins-grid {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 12px;
          align-content: start;
        }

        .pss-loading, .pss-empty {
          grid-column: 1 / -1;
          text-align: center;
          color: #666;
          padding: 40px;
        }

        .pss-skin-card {
          position: relative;
          background: #16162a;
          border: 2px solid transparent;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pss-skin-card:hover {
          border-color: #3a3a5a;
        }

        .pss-skin-card.pss-selected {
          border-color: #6c8cff;
          background: rgba(108, 140, 255, 0.1);
        }

        .pss-checkbox {
          position: absolute;
          top: 6px;
          left: 6px;
          width: 20px;
          height: 20px;
          background: #0d0d1a;
          border: 2px solid #3a3a5a;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1;
        }

        .pss-selected .pss-checkbox {
          background: #6c8cff;
          border-color: #6c8cff;
        }

        .pss-checkbox svg {
          color: #fff;
        }

        .pss-skin-image {
          width: 100%;
          aspect-ratio: 3/4;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0d0d1a;
          border-radius: 4px;
          overflow: hidden;
        }

        .pss-skin-image img {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }

        .pss-skin-placeholder {
          color: #444;
          font-size: 24px;
        }

        .pss-skin-name {
          text-align: center;
          font-size: 11px;
          color: #888;
          margin-top: 6px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .pss-footer {
          padding: 16px 20px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pss-generate-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px;
          background: #6c8cff;
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pss-generate-btn:hover:not(:disabled) {
          background: #5a7aee;
        }

        .pss-generate-btn:disabled {
          background: #3a3a5a;
          color: #666;
          cursor: not-allowed;
        }

        .pss-progress {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .pss-progress-bar {
          height: 8px;
          background: #2a2a4a;
          border-radius: 4px;
          overflow: hidden;
        }

        .pss-progress-fill {
          height: 100%;
          background: #6c8cff;
          transition: width 0.3s ease;
        }

        .pss-progress span {
          text-align: center;
          color: #888;
          font-size: 13px;
        }

        .pss-results {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .pss-results span {
          font-size: 14px;
        }

        .pss-results.pss-success span {
          color: #4caf50;
        }

        .pss-results.pss-error span {
          color: #f44336;
        }

        .pss-results button {
          padding: 8px 16px;
          background: #2a2a4a;
          border: none;
          border-radius: 4px;
          color: #ccc;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pss-results button:hover {
          background: #3a3a5a;
          color: #fff;
        }
      `}</style>
    </div>
  )
}
