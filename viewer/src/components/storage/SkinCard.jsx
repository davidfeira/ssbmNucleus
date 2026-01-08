/**
 * SkinCard - Individual costume card component
 *
 * Features:
 * - CSP image display with fallback
 * - Stock icon overlay
 * - Drag and drop support
 * - Context menu (right-click)
 * - Edit button
 */
export default function SkinCard({
  skin,
  selectedCharacter,
  folderId,
  displayIdx,
  arrayIdx,
  isDragging,
  reordering,
  lastImageUpdate,
  onDragStart,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop,
  onDragEnd,
  onContextMenu,
  onEditClick,
  API_URL
}) {
  return (
    <div
      key={skin.id}
      className={`skin-card ${isDragging ? 'dragging' : ''} ${folderId ? 'in-folder' : ''}`}
      draggable={!reordering}
      onDragStart={(e) => onDragStart(e, arrayIdx)}
      onDragOver={onDragOver}
      onDragEnter={(e) => onDragEnter(e, displayIdx)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, displayIdx)}
      onDragEnd={onDragEnd}
      onContextMenu={(e) => onContextMenu(e, skin, arrayIdx)}
      style={{ opacity: isDragging ? 0.5 : 1 }}
    >
      <div className="skin-image-container">
        {skin.has_csp ? (
          <img
            src={`${API_URL.replace('/api/mex', '')}/storage/${selectedCharacter}/${skin.id}_csp.png?t=${lastImageUpdate}`}
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
        {skin.has_stock && (
          <div className="stock-overlay">
            <img
              src={`${API_URL.replace('/api/mex', '')}/storage/${selectedCharacter}/${skin.id}_stc.png?t=${lastImageUpdate}`}
              alt={`${selectedCharacter} stock`}
              className="stock-overlay-img"
            />
          </div>
        )}
        <button
          className="btn-edit"
          onClick={(e) => {
            e.stopPropagation()
            e.preventDefault()
            onEditClick('costume', {
              id: skin.id,
              character: selectedCharacter,
              color: skin.color,
              has_csp: skin.has_csp,
              has_stock: skin.has_stock,
              cspUrl: `${API_URL.replace('/api/mex', '')}/storage/${selectedCharacter}/${skin.id}_csp.png`,
              stockUrl: skin.has_stock ? `${API_URL.replace('/api/mex', '')}/storage/${selectedCharacter}/${skin.id}_stc.png` : null,
              slippi_safe: skin.slippi_safe,
              slippi_tested: skin.slippi_tested,
              slippi_manual_override: skin.slippi_manual_override,
              has_hd_csp: skin.has_hd_csp,
              hd_csp_resolution: skin.hd_csp_resolution,
              hd_csp_size: skin.hd_csp_size,
              // Alternate CSPs from batch pose generation (metadata uses snake_case)
              alternateCsps: (skin.alternate_csps || []).map(alt => ({
                id: alt.id,
                url: `/storage/${selectedCharacter}/${alt.filename}`,
                poseName: alt.pose_name,
                isHd: alt.is_hd,
                timestamp: alt.timestamp
              }))
            })
          }}
          title="Edit costume"
        >
          ✎
        </button>
      </div>

      <div className="skin-info">
        <div className="skin-color">{skin.color}</div>
      </div>
    </div>
  )
}
