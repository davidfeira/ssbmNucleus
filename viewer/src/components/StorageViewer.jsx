import { useState } from 'react'
import './StorageViewer.css'
import { DEFAULT_CHARACTERS } from '../defaultCharacters'

export default function StorageViewer({ metadata }) {
  const [selectedCharacter, setSelectedCharacter] = useState(null)

  // Merge default characters with metadata
  // Always show all 26 vanilla characters, even if they don't have custom skins
  const allCharacters = { ...metadata?.characters }

  // Add any missing default characters with 0 skins
  Object.keys(DEFAULT_CHARACTERS).forEach(charName => {
    if (!allCharacters[charName]) {
      allCharacters[charName] = { skins: [] }
    }
  })

  const characters = Object.keys(allCharacters).sort()
  const totalSkins = characters.reduce((sum, char) => {
    return sum + (allCharacters[char]?.skins?.length || 0)
  }, 0)

  // If a character is selected, show their skins
  if (selectedCharacter) {
    const charData = allCharacters[selectedCharacter]
    const skinCount = charData?.skins?.length || 0

    return (
      <div className="storage-viewer">
        <div className="character-detail">
          <button
            onClick={() => setSelectedCharacter(null)}
            className="back-button"
          >
            ← Back to Characters
          </button>

          <h2>{selectedCharacter}</h2>
          <p className="skin-count">{skinCount} skin{skinCount !== 1 ? 's' : ''}</p>

          {skinCount === 0 ? (
            <div className="no-skins-message">
              <p>No custom skins yet. Add some using the intake system!</p>
            </div>
          ) : (
            <div className="skins-grid">
              {charData.skins.map((skin) => (
                <div key={skin.id} className="skin-card">
                  <div className="skin-header">
                    <h4 className="skin-title">{selectedCharacter} - {skin.color}</h4>
                  </div>

                  <div className="skin-images">
                    <div className="skin-image-container">
                      {skin.has_csp ? (
                        <img
                          src={`/storage/${selectedCharacter}/${skin.id}_csp.png`}
                          alt={`${selectedCharacter} - ${skin.color}`}
                          className="skin-csp"
                          onError={(e) => {
                            e.target.style.display = 'none'
                            e.target.nextSibling.style.display = 'flex'
                          }}
                        />
                      ) : null}
                      <div className="skin-placeholder" style={{ display: skin.has_csp ? 'none' : 'flex' }}>
                        <span className="skin-initial">{skin.color[0]}</span>
                      </div>
                      <div className="image-label">CSP</div>
                    </div>

                    {skin.has_stock && (
                      <div className="stock-container">
                        <img
                          src={`/storage/${selectedCharacter}/${skin.id}_stc.png`}
                          alt={`${selectedCharacter} stock`}
                          className="skin-stock"
                        />
                        <div className="image-label">Stock</div>
                      </div>
                    )}
                  </div>

                  <div className="skin-info">
                    <div className="skin-color">{skin.color}</div>
                    <div className="skin-id">{skin.id}</div>
                    <div className="skin-sources">
                      <div className="source-line">CSP: {skin.csp_source}</div>
                      <div className="source-line">Stock: {skin.stock_source}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Character selection grid
  return (
    <div className="storage-viewer">
      <div className="storage-stats">
        <div className="stat-card">
          <div className="stat-value">{characters.length}</div>
          <div className="stat-label">Characters</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalSkins}</div>
          <div className="stat-label">Total Skins</div>
        </div>
      </div>

      <div className="characters-grid">
        {characters.map((characterName) => {
          const charData = allCharacters[characterName]
          const skinCount = charData?.skins?.length || 0

          // Find default color skin (color === "Default") to get costume code
          const defaultSkin = charData?.skins?.find(s => s.color === 'Default')
                            || charData?.skins?.[0]

          // Determine costume code: from skin metadata or from DEFAULT_CHARACTERS
          const costumeCode = defaultSkin?.costume_code || DEFAULT_CHARACTERS[characterName]?.defaultCostume

          // ALWAYS use vanilla CSP on homepage for consistency (like vanilla game)
          const vanillaCspPath = costumeCode
            ? `/vanilla/${characterName}/${costumeCode}/csp.png`
            : null

          return (
            <div
              key={characterName}
              className="character-card"
              onClick={() => setSelectedCharacter(characterName)}
            >
              <div className="character-image-container">
                {vanillaCspPath ? (
                  <img
                    src={vanillaCspPath}
                    alt={characterName}
                    className="character-csp"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextSibling.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div className="character-placeholder" style={{ display: vanillaCspPath ? 'none' : 'flex' }}>
                  <span className="character-initial">{characterName[0]}</span>
                </div>
              </div>

              <h3 className="character-name">{characterName}</h3>
              <p className="skin-count">{skinCount} skin{skinCount !== 1 ? 's' : ''}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
