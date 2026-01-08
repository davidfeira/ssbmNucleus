/**
 * CharactersGrid - Character grid display
 *
 * Features:
 * - Grid layout of character cards
 * - CSS icon display with fallback
 * - Skin count display
 * - Skeleton loading state
 * - Click to select character
 */

const BACKEND_URL = 'http://127.0.0.1:5000'

const SkeletonCard = () => (
  <div className="character-card skeleton-card">
    <div className="character-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '50%', height: '12px' }}></div>
  </div>
)

export default function CharactersGrid({ characters, allCharacters, isLoading, onSelectCharacter }) {
  return (
    <div className="grid-wrapper">
      <div className="characters-grid">
        {isLoading ? (
          // Skeleton loading for characters
          Array.from({ length: 12 }).map((_, idx) => (
            <SkeletonCard key={`skeleton-${idx}`} />
          ))
        ) : characters.map((characterName) => {
          const charData = allCharacters[characterName]
          // Only count visible skins (exclude hidden Ice Climbers Nana entries)
          const visibleSkins = charData?.skins?.filter(skin => skin.visible !== false) || []
          const skinCount = visibleSkins.length

          // Use CSS icon which already includes character name
          const cssIconPath = `${BACKEND_URL}/vanilla/${characterName}/css_icon.png`

          return (
            <div
              key={characterName}
              className="character-card"
              onClick={() => onSelectCharacter(characterName)}
            >
              <div className="character-icon-container">
                <img
                  src={cssIconPath}
                  alt={characterName}
                  className="character-css-icon"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
                <div className="character-placeholder" style={{ display: 'none' }}>
                  <span className="character-initial">{characterName[0]}</span>
                </div>
              </div>

              <p className="skin-count"><span>{skinCount}</span> skin{skinCount !== 1 ? 's' : ''}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
