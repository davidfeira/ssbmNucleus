import { playSound, playHoverSound } from '../../utils/sounds'

const SkeletonCard = () => (
  <div className="stage-card skeleton-card">
    <div className="stage-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '60%', height: '12px' }}></div>
  </div>
)

export default function CustomStagesGrid({
  customStages,
  isLoading,
  onSelectStage,
  onBack,
  onImportZip,
  onScanProject,
  importing
}) {
  return (
    <div className="grid-wrapper">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className="mode-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('back'); onBack(); }}
        >
          ← Back to Stages
        </button>

        <div className="import-file-container" style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <label
            className="intake-import-btn"
            style={{ cursor: importing ? 'not-allowed' : 'pointer', opacity: importing ? 0.6 : 1 }}
            onMouseEnter={playHoverSound}
            onClick={() => { if (!importing) playSound('start'); }}
          >
            {importing ? 'Importing...' : 'Import ZIP'}
            <input
              type="file"
              accept=".zip"
              onChange={onImportZip}
              disabled={importing}
              style={{ display: 'none' }}
            />
          </label>
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); onScanProject(); }}
            disabled={importing}
          >
            Scan Project
          </button>
        </div>
      </div>

      <div className="custom-stages-grid">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, idx) => (
            <SkeletonCard key={`skeleton-cs-${idx}`} />
          ))
        ) : customStages.length === 0 ? (
          <div className="no-skins-message" style={{ gridColumn: '1 / -1' }}>
            <p>No custom stages yet. Import a stage package or scan a project.</p>
          </div>
        ) : customStages.map((stage) => (
          <div
            key={stage.slug}
            className="stage-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); onSelectStage(stage); }}
          >
            <div className="stage-icon-container">
              {stage.has_icon ? (
                <img
                  src={stage.icon_url}
                  alt={stage.name}
                  className="stage-icon"
                  style={{ imageRendering: 'pixelated' }}
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
              ) : null}
              <div className="stage-placeholder" style={{ display: stage.has_icon ? 'none' : 'flex' }}>
                {stage.name[0]}
              </div>
            </div>
            <div className="stage-info">
              <h3 className="stage-name">{stage.name}</h3>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
