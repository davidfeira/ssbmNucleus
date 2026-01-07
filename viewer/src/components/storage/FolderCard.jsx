/**
 * FolderCard - Folder card component with inline editing
 *
 * Features:
 * - Expandable/collapsible folder
 * - Inline name editing
 * - Drag and drop support
 * - Rename and delete actions
 * - Skin count display
 */
export default function FolderCard({
  folder,
  isExpanded,
  displayIdx,
  arrayIdx,
  isDragging,
  isEditing,
  editingFolderName,
  folderSkinCount,
  reordering,
  onToggle,
  onDragStart,
  onDragOver,
  onDragEnter,
  onDragLeave,
  onDrop,
  onDragEnd,
  onEditingFolderNameChange,
  onSaveFolderName,
  onCancelEdit,
  onStartEditing,
  onDelete,
  justDraggedRef
}) {
  return (
    <div
      key={folder.id}
      className={`folder-card ${isExpanded ? 'expanded' : ''} ${isDragging ? 'dragging' : ''}`}
      draggable={!reordering && !isEditing}
      onDragStart={(e) => onDragStart(e, arrayIdx)}
      onDragOver={onDragOver}
      onDragEnter={(e) => onDragEnter(e, displayIdx)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, displayIdx)}
      onDragEnd={onDragEnd}
      onClick={() => !isEditing && !justDraggedRef.current && onToggle(folder.id)}
    >
      <svg className="folder-icon" viewBox="0 0 24 24" fill="currentColor">
        {isExpanded ? (
          <path d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/>
        ) : (
          <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
        )}
      </svg>
      <div className="folder-header">
        {isEditing ? (
          <input
            className="folder-name-input"
            value={editingFolderName}
            onChange={(e) => onEditingFolderNameChange(e.target.value)}
            onBlur={() => onSaveFolderName(folder.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSaveFolderName(folder.id)
              if (e.key === 'Escape') onCancelEdit()
            }}
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="folder-name">{folder.name}</span>
        )}
        <span className="folder-count">{folderSkinCount} skin{folderSkinCount !== 1 ? 's' : ''}</span>
        <span className="folder-chevron">▼</span>
      </div>
      <div className="folder-actions">
        <button
          onClick={(e) => {
            e.stopPropagation()
            onStartEditing(folder)
          }}
          title="Rename folder"
        >
          ✎
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete(folder.id)
          }}
          title="Delete folder"
        >
          ×
        </button>
      </div>
    </div>
  )
}
