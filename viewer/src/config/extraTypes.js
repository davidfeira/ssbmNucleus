/**
 * Extra types configuration for character-specific mods
 * Each extra type defines editable properties that modify specific dat file offsets
 */

// NOTE: Offsets are character-specific - do not copy between characters
export const EXTRA_TYPES = {
  Falco: [
    {
      id: 'laser',
      name: 'Laser Color',
      description: 'Change laser beam colors',
      targetFile: 'PlFc.dat',
      icon: 'laser',
      // Offset definitions for the 98 matrix format (Falco-specific)
      offsets: {
        wide: { start: 0x13440, end: 0x13490 },
        thin: { start: 0x134E0, end: 0x13530 },
        outline: { start: 0x13580, end: 0x135D0 }
      },
      properties: [
        { id: 'wide', name: 'Wide Layer', description: 'Transparent outer glow' },
        { id: 'thin', name: 'Thin Layer', description: 'Semi-transparent middle' },
        { id: 'outline', name: 'Outline', description: 'Opaque inner core' }
      ]
    }
  ]
  // Fox laser offsets would be different - add when discovered
}

/**
 * Check if a character has any extras available
 * @param {string} character - Character name
 * @returns {boolean}
 */
export function hasExtras(character) {
  return EXTRA_TYPES[character]?.length > 0
}

/**
 * Get all extra types for a character
 * @param {string} character - Character name
 * @returns {Array}
 */
export function getExtraTypes(character) {
  return EXTRA_TYPES[character] || []
}

/**
 * Get a specific extra type by id
 * @param {string} character - Character name
 * @param {string} typeId - Extra type id (e.g., 'laser')
 * @returns {Object|null}
 */
export function getExtraType(character, typeId) {
  const types = EXTRA_TYPES[character] || []
  return types.find(t => t.id === typeId) || null
}
