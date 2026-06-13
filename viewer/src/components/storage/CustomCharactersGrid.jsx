import { playSound, playHoverSound } from '../../utils/sounds'

const SkeletonCard = () => (
  <div className="character-card skeleton-card">
    <div className="character-icon-container">
      <div className="skeleton skeleton-image"></div>
    </div>
    <div className="skeleton skeleton-text" style={{ width: '60%', height: '12px' }}></div>
  </div>
)

export default function CustomCharactersGrid({
  customCharacters,
  isLoading,
  onSelectCharacter,
  onBack
}) {
  return (
    <div className="grid-wrapper">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className="mode-btn"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('back'); onBack(); }}
        >
          ← Back to Characters
        </button>
      </div>

      <div className="characters-grid custom-characters-grid">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, idx) => (
            <SkeletonCard key={`skeleton-cc-${idx}`} />
          ))
        ) : customCharacters.length === 0 ? (
          <div className="no-skins-message" style={{ width: '100%' }}>
            <p>No custom characters yet. Import a fighter package or scan an ISO.</p>
          </div>
        ) : customCharacters.map((char) => (
          <div
            key={char.slug}
            className="character-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); onSelectCharacter(char); }}
          >
            <div className="character-icon-container">
              {char.has_css_icon ? (
                <img
                  src={char.icon_url}
                  alt={char.name}
                  className="character-css-icon"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.nextSibling.style.display = 'flex'
                  }}
                />
              ) : null}
              <div className="character-placeholder" style={{ display: char.has_css_icon ? 'none' : 'flex' }}>
                <span className="character-initial">{char.name[0]}</span>
              </div>
            </div>
            <p className="skin-count">
              <span>{char.costume_count}</span> costume{char.costume_count !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
