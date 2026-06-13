/**
 * useFolderManagement Hook
 *
 * Manages folder operations for the storage viewer including:
 * - Creating, renaming, deleting folders
 * - Toggling folder expand/collapse state
 * - Edit state for folder rename UI
 *
 * Works for both character skin folders and DAS stage variant folders. The
 * caller selects which by passing `idField` ('character' or 'stageFolder'),
 * `idValue`, and the matching `routes` group. Defaults target character skins.
 */

import { useState } from 'react'

const CHARACTER_ROUTES = {
  create: '/storage/folders/create',
  rename: '/storage/folders/rename',
  delete: '/storage/folders/delete',
  toggle: '/storage/folders/toggle'
}

export function useFolderManagement({
  // Identity of the thing the folders belong to. `idField` is the body key the
  // backend expects ('character' for skins, 'stageFolder' for stage variants).
  idField = 'character',
  idValue,
  // Back-compat alias used by the character detail view.
  selectedCharacter,
  routes = CHARACTER_ROUTES,
  API_URL,
  onRefresh,
  // Optional externally-owned expansion state. StorageViewer owns this so it
  // persists when the detail view (which calls this hook) unmounts on Back.
  expandedFolders: externalExpandedFolders,
  setExpandedFolders: externalSetExpandedFolders
}) {
  const ownerId = idValue !== undefined ? idValue : selectedCharacter
  // Folder state
  const [internalExpandedFolders, setInternalExpandedFolders] = useState({}) // { folderId: true/false }
  const expandedFolders = externalExpandedFolders !== undefined ? externalExpandedFolders : internalExpandedFolders
  const setExpandedFolders = externalSetExpandedFolders || setInternalExpandedFolders
  const [editingFolderId, setEditingFolderId] = useState(null)
  const [editingFolderName, setEditingFolderName] = useState('')

  // Toggle folder expand/collapse. currentExpanded is the state the folder is
  // DISPLAYED with (which falls back to the persisted metadata value when the
  // folder was never toggled this session) — deriving the toggle from local
  // state alone made the first click on a persisted-closed folder a no-op.
  const toggleFolder = async (folderId, currentExpanded) => {
    // Update local state immediately for responsive UI
    setExpandedFolders(prev => ({
      ...prev,
      [folderId]: currentExpanded !== undefined ? !currentExpanded : !(prev[folderId] ?? true)
    }))

    // Also persist to backend
    try {
      await fetch(`${API_URL}${routes.toggle}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [idField]: ownerId,
          folderId
        })
      })
    } catch (err) {
      console.error('Toggle folder error:', err)
    }
  }

  // Create new folder
  const handleCreateFolder = async () => {
    try {
      const response = await fetch(`${API_URL}${routes.create}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [idField]: ownerId,
          name: 'New Folder'
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
        // Start editing the new folder name
        setEditingFolderId(data.folder.id)
        setEditingFolderName(data.folder.name)
      } else {
        alert(`Create folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Create folder error:', err)
      alert(`Create folder error: ${err.message}`)
    }
  }

  // Start editing folder name
  const startEditingFolder = (folder) => {
    setEditingFolderId(folder.id)
    setEditingFolderName(folder.name)
  }

  // Save folder name after edit
  const saveFolderName = async (folderId) => {
    if (!editingFolderName.trim()) {
      setEditingFolderId(null)
      return
    }

    try {
      const response = await fetch(`${API_URL}${routes.rename}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [idField]: ownerId,
          folderId,
          newName: editingFolderName.trim()
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
      } else {
        alert(`Rename folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Rename folder error:', err)
      alert(`Rename folder error: ${err.message}`)
    } finally {
      setEditingFolderId(null)
      setEditingFolderName('')
    }
  }

  // Delete folder (contents are moved out, not deleted)
  const deleteFolder = async (folderId) => {
    if (!confirm('Delete this folder? Contents will be moved out, not deleted.')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}${routes.delete}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [idField]: ownerId,
          folderId
        })
      })

      const data = await response.json()

      if (data.success) {
        await onRefresh()
      } else {
        alert(`Delete folder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Delete folder error:', err)
      alert(`Delete folder error: ${err.message}`)
    }
  }

  return {
    // State
    expandedFolders,
    setExpandedFolders,
    editingFolderId,
    setEditingFolderId,
    editingFolderName,
    setEditingFolderName,

    // Handlers
    toggleFolder,
    handleCreateFolder,
    startEditingFolder,
    saveFolderName,
    deleteFolder
  }
}
