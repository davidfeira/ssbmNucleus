// Bottom texture strip: thumbnails of all model textures.
export default function TextureStrip({
  height,
  modelTextures,
  selectedTextureIndex,
  onSelectTexture,
  editedTextures
}) {
  return (
    <div className="skin-creator-texture-strip" style={{ height }}>
      <div className="skin-creator-panel-header">Textures ({modelTextures.length})</div>
      <div className="skin-creator-texture-list">
        {modelTextures.length === 0 ? (
          <div className="texture-loading">Loading textures...</div>
        ) : (
          modelTextures.map((tex, idx) => (
            <div
              key={idx}
              className={`skin-creator-texture-item ${selectedTextureIndex === idx ? 'selected' : ''} ${editedTextures[idx] ? 'edited' : ''}`}
              onClick={() => onSelectTexture(idx)}
            >
              <div className="texture-thumbnail">
                {editedTextures[idx] ? (
                  <img
                    src={editedTextures[idx]}
                    alt={tex.name}
                    style={{
                      aspectRatio: `${tex.width} / ${tex.height}`
                    }}
                  />
                ) : tex.thumbnail && (
                  <img
                    src={`data:image/png;base64,${tex.thumbnail}`}
                    alt={tex.name}
                    style={{
                      aspectRatio: `${tex.width} / ${tex.height}`
                    }}
                  />
                )}
              </div>
              <div className="texture-info">
                <span className="texture-name">{tex.name}{editedTextures[idx] && ' *'}</span>
                <span className="texture-size">{tex.width}x{tex.height}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
