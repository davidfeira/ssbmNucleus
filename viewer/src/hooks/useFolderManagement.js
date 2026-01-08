/**
 * useFolderManagement Hook
 *
 * Manages folder operations for the storage viewer including:
 * - Creating, renaming, deleting folders
 * - Toggling folder expand/collapse state
 * - Edit state for folder rename UI
 */

import { useState } from 'react'

export function useFolderManagement({
  selectedCharacter,
  API_URL,
  onRefresh
}) {
  // Folder state
  const [expandedFolders, setExpandedFolders] = useState({}) // { folderId: true/false }
  const [editingFolderId, setEditingFolderId] = useState(null)
  const [editingFolderName, setEditingFolderName] = useState('')

  // Toggle folder expand/collapse
  const toggleFolder = async (folderId) => {
    // Update local state immediately for responsive UI
    setExpandedFolders(prev => ({
      ...prev,
      [folderId]: !(prev[folderId] ?? true)
    }))

    // Also persist to backend
    try {
      await fetch(`${API_URL}/storage/folders/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
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
      const response = await fetch(`${API_URL}/storage/folders/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
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
      const response = await fetch(`${API_URL}/storage/folders/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
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
      const response = await fetch(`${API_URL}/storage/folders/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedCharacter,
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
