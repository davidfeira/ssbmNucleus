/**
 * Storage Viewer Utility Functions
 *
 * Pure utility functions for managing skin/variant display lists and folder organization
 */

/**
 * Build display list from allSkins array with folder expansion state
 * @param {Array} allSkins - Array of skins and folders
 * @param {Object} expandedFolders - Map of folderId -> isExpanded
 * @returns {Array} Display list with type, item, arrayIndex
 */
export const buildDisplayList = (allSkins, expandedFolders = {}) => {
  if (!allSkins?.length) return []

  // Build folder info and collect folder items
  const folderItems = {} // folderId -> [items with arrayIndex]
  const folders = [] // folder objects with arrayIndex
  const rootItems = [] // items not in any folder

  for (let i = 0; i < allSkins.length; i++) {
    const item = allSkins[i]

    if (item.type === 'folder') {
      folders.push({ folder: item, arrayIndex: i })
      folderItems[item.id] = []
    } else if (item.visible !== false) {
      if (item.folder_id) {
        if (!folderItems[item.folder_id]) {
          folderItems[item.folder_id] = []
        }
        folderItems[item.folder_id].push({ skin: item, arrayIndex: i })
      } else {
        rootItems.push({ skin: item, arrayIndex: i })
      }
    }
  }

  // Build display list: root items first, then folders with their items
  const result = []

  // Add root items that come before all folders
  // We need to maintain relative order, so track what we've added
  const addedIndices = new Set()

  // Go through array in order to maintain relative positioning
  for (let i = 0; i < allSkins.length; i++) {
    const item = allSkins[i]

    if (item.type === 'folder') {
      const isExpanded = expandedFolders[item.id] ?? item.expanded ?? true
      result.push({ type: 'folder', folder: item, isExpanded, arrayIndex: i })
      addedIndices.add(i)

      // If expanded, add all items belonging to this folder right after it
      if (isExpanded && folderItems[item.id]) {
        for (const folderItem of folderItems[item.id]) {
          result.push({ type: 'skin', skin: folderItem.skin, folderId: item.id, arrayIndex: folderItem.arrayIndex })
          addedIndices.add(folderItem.arrayIndex)
        }
      }
    } else if (item.visible !== false && !item.folder_id) {
      // Root item - add it
      result.push({ type: 'skin', skin: item, folderId: null, arrayIndex: i })
      addedIndices.add(i)
    }
    // Skip folder items here - they're added after their folder
  }

  return result
}

/**
 * Count skins in a folder (by folder_id)
 * @param {string} folderId - Folder ID
 * @param {Array} allSkins - Array of skins
 * @returns {number} Count of visible skins in folder
 */
export const countSkinsInFolder = (folderId, allSkins) => {
  return allSkins.filter(s => s.folder_id === folderId && s.visible !== false).length
}

/**
 * Determine folder membership based on position after reorder
 * Returns the folder_id the item should have at the given position
 * @param {Array} allSkins - Array of skins
 * @param {number} position - Position index
 * @returns {string|null} Folder ID or null for root
 */
export const getFolderIdAtPosition = (allSkins, position) => {
  // Look backwards from position to find the context
  // If we find a skin with folder_id before hitting a folder or start, we're in that folder
  // If we find a folder, we're right after it (in that folder)
  // If we hit start or a skin without folder_id, we're at root
  for (let i = position - 1; i >= 0; i--) {
    const item = allSkins[i]
    if (item.type === 'folder') {
      // We're right after a folder - in that folder
      return item.id
    }
    if (item.folder_id) {
      // Previous item is in a folder - we're in that folder too
      return item.folder_id
    }
    // Previous item is at root level - we're at root
    return null
  }
  return null // At the start, root level
}
