/**
 * StagesGrid - Stage grid display
 *
 * Features:
 * - Grid layout of stage cards
 * - Stage icon display with fallback
 * - Variant count display
 * - Skeleton loading state
 * - Click to select stage
 */

const BACKEND_URL = 'http://127.0.0.1:5000'

const DAS_STAGES = [
  { code: 'GrOp', name: 'Dreamland', folder: 'dreamland', vanillaImage: `${BACKEND_URL}/vanilla/stages/dreamland.png` },
  { code: 'GrPs', name: 'Pokemon Stadium', folder: 'pokemon_stadium', vanillaImage: `${BACKEND_URL}/vanilla/stages/pokemon stadium.png` },
  { code: 'GrSt', name: "Yoshi's Story", folder: 'yoshis_story', vanillaImage: `${BACKEND_URL}/vanilla/stages/yoshis story.png` },
  { code: 'GrNBa', name: 'Battlefield', folder: 'battlefield', vanillaImage: `${BACKEND_URL}/vanilla/stages/battlefield.png` },
  { code: 'GrIz', name: 'Fountain of Dreams', folder: 'fountain_of_dreams', vanillaImage: `${BACKEND_URL}/vanilla/stages/fountain of dreams.png` },
  { code: 'GrNLa', name: 'Final Destination', folder: 'final_destination', vanillaImage: `${BACKEND_URL}/vanilla/stages/final destination.png` }
]

export default function StagesGrid({ stageVariants, isLoading, onSelectStage }) {
  return (
    <div className="grid-wrapper">
      <div className="stages-grid">
        {isLoading ? (
          // Skeleton loading for stages
          Array.from({ length: 6 }).map((_, idx) => (
            <div key={`skeleton-stage-${idx}`} className="stage-skeleton">
              <div className="skeleton-icon"></div>
              <div className="skeleton-text" style={{ width: '70%' }}></div>
              <div className="skeleton-text" style={{ width: '40%' }}></div>
            </div>
          ))
        ) : DAS_STAGES.map((stage) => {
          const variants = stageVariants[stage.code] || []
          const variantCount = variants.length
          const vanillaImagePath = stage.vanillaImage

          return (
            <div
              key={stage.code}
              className="stage-card"
              onClick={() => onSelectStage(stage)}
            >
              <div className="stage-icon-container">
                <img
                  src={vanillaImagePath}
                  alt={stage.name}
                  className="stage-icon"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
                <div className="stage-placeholder" style={{ display: 'none' }}>
                  {stage.name[0]}
                </div>
              </div>

              <div className="stage-info">
                <h3 className="stage-name">{stage.name}</h3>
                <p className="stage-variant-count">
                  <span>{variantCount}</span> variant{variantCount !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
