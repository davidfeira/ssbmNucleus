/**
 * Extra types configuration for character-specific mods
 * Each extra type defines editable properties that modify specific dat file offsets
 */

// NOTE: Offsets are character-specific - do not copy between characters
export const EXTRA_TYPES = {
  Marth: [
    {
      id: 'sword',
      name: 'Sword Trail',
      description: 'Sword swing trail colors',
      targetFile: 'PlMs.dat',
      icon: 'sword',
      // 9 bytes: 3x RGB colors for sword trail gradient
      offsets: {
        main: { start: 0x3948, size: 3, format: 'RGB' },
        secondary: { start: 0x394B, size: 3, format: 'RGB' },
        tertiary: { start: 0x394E, size: 3, format: 'RGB' }
      },
      vanilla: {
        main: 'FF0000',      // Red
        secondary: 'FFFF00', // Yellow
        tertiary: 'FFFFFF'   // White
      },
      properties: [
        { id: 'main', name: 'Main', description: 'Primary trail color', format: 'RGB' },
        { id: 'secondary', name: 'Secondary', description: 'Middle gradient color', format: 'RGB' },
        { id: 'tertiary', name: 'Edge', description: 'Outer edge color', format: 'RGB' }
      ]
    }
  ],
  Roy: [
    {
      id: 'sword',
      name: 'Sword Trail',
      description: 'Sword swing trail colors',
      targetFile: 'PlFe.dat',
      icon: 'sword',
      offsets: {
        main: { start: 0x3AA0, size: 3, format: 'RGB' },
        secondary: { start: 0x3AA3, size: 3, format: 'RGB' },
        tertiary: { start: 0x3AA6, size: 3, format: 'RGB' }
      },
      vanilla: {
        main: 'FF00EB',      // Magenta/Pink
        secondary: '785000', // Brown/Orange
        tertiary: 'FFFFFF'   // White
      },
      properties: [
        { id: 'main', name: 'Main', description: 'Primary trail color', format: 'RGB' },
        { id: 'secondary', name: 'Secondary', description: 'Middle gradient color', format: 'RGB' },
        { id: 'tertiary', name: 'Edge', description: 'Outer edge color', format: 'RGB' }
      ]
    }
  ],
  Link: [
    {
      id: 'sword',
      name: 'Sword Trail',
      description: 'Sword swing trail colors',
      targetFile: 'PlLk.dat',
      icon: 'sword',
      offsets: {
        main: { start: 0x35EC, size: 3, format: 'RGB' },
        secondary: { start: 0x35EF, size: 3, format: 'RGB' },
        tertiary: { start: 0x35F2, size: 3, format: 'RGB' }
      },
      vanilla: {
        main: 'FF0000',      // Red
        secondary: 'FFFF00', // Yellow
        tertiary: 'FFFFFF'   // White
      },
      properties: [
        { id: 'main', name: 'Main', description: 'Primary trail color', format: 'RGB' },
        { id: 'secondary', name: 'Secondary', description: 'Middle gradient color', format: 'RGB' },
        { id: 'tertiary', name: 'Edge', description: 'Outer edge color', format: 'RGB' }
      ]
    }
  ],
  'Young Link': [
    {
      id: 'sword',
      name: 'Sword Trail',
      description: 'Sword swing trail colors',
      targetFile: 'PlCl.dat',
      icon: 'sword',
      offsets: {
        main: { start: 0x3790, size: 3, format: 'RGB' },
        secondary: { start: 0x3793, size: 3, format: 'RGB' },
        tertiary: { start: 0x3796, size: 3, format: 'RGB' }
      },
      vanilla: {
        main: 'FF0000',      // Red
        secondary: 'FFFF00', // Yellow
        tertiary: 'FFFFFF'   // White
      },
      properties: [
        { id: 'main', name: 'Main', description: 'Primary trail color', format: 'RGB' },
        { id: 'secondary', name: 'Secondary', description: 'Middle gradient color', format: 'RGB' },
        { id: 'tertiary', name: 'Edge', description: 'Outer edge color', format: 'RGB' }
      ]
    }
  ],
  Pikachu: [
    {
      id: 'thunder',
      name: 'Thunder',
      description: 'Down-B Thunder bolt colors',
      targetFile: 'PlPk.dat',
      icon: 'thunder',
      format: '07_07_07',
      shared: true,
      sharedWith: ['Pichu'],
      owner: 'Pikachu',
      offsets: {
        color1: { start: 0xC358, size: 3, format: 'RGB' },
        color2: { start: 0xC35C, size: 3, format: 'RGB' }
      },
      vanilla: {
        color1: 'FFFFFF',  // White
        color2: 'FFFF00'   // Yellow
      },
      properties: [
        { id: 'color1', name: 'Primary', description: 'Main bolt color', format: 'RGB' },
        { id: 'color2', name: 'Secondary', description: 'Bolt glow color', format: 'RGB' }
      ]
    }
  ],
  Mewtwo: [
    {
      id: 'shadow_ball',
      name: 'Shadow Ball',
      description: 'Shadow Ball colors',
      targetFile: 'PlMt.dat',
      icon: 'shadowball',
      format: 'direct_rgb',
      offsets: {
        color1: { start: 0x100B0, size: 3, format: 'RGB' },
        color2: { start: 0x100B4, size: 3, format: 'RGB' }
      },
      vanilla: {
        color1: 'FFFFFF',  // White
        color2: '0000FF'   // Blue
      },
      properties: [
        { id: 'color1', name: 'Primary', description: 'Main ball color', format: 'RGB' },
        { id: 'color2', name: 'Secondary', description: 'Inner glow color', format: 'RGB' }
      ]
    }
  ],
  Falco: [
    {
      id: 'laser',
      name: 'Laser Color',
      description: 'Change laser beam colors',
      targetFile: 'PlFc.dat',
      icon: 'laser',
      // Offset definitions for the 98 matrix format (Falco-specific)
      offsets: {
        wide: { start: 0x13440, end: 0x134A0 },
        thin: { start: 0x134E0, end: 0x13540 },
        outline: { start: 0x13580, end: 0x135E0 }
      },
      properties: [
        { id: 'wide', name: 'Wide Layer', description: 'Transparent outer glow' },
        { id: 'thin', name: 'Thin Layer', description: 'Semi-transparent middle' },
        { id: 'outline', name: 'Outline', description: 'Opaque inner core' }
      ]
    },
    {
      id: 'sideb',
      name: 'Side-B Color',
      description: 'Phantasm afterimage colors',
      targetFile: 'PlFc.dat',
      icon: 'sideb',
      format: '42_48',
      // 42_48 format: 3 RGBA colors
      offsets: {
        primary: { start: 0x1EC48, size: 4 },
        secondary: { start: 0x1EC4C, size: 4 },
        tertiary: { start: 0x1EC50, size: 4 }
      },
      vanilla: {
        primary: '0099FFFF',
        secondary: 'CCE6FFFF',
        tertiary: 'FFFFFFFF'
      },
      properties: [
        { id: 'primary', name: 'Primary', description: 'Main afterimage color' },
        { id: 'secondary', name: 'Secondary', description: 'Edge/gradient color' },
        { id: 'tertiary', name: 'Glow', description: 'Outer glow color' }
      ]
    },
    {
      id: 'gun',
      name: 'Gun Model',
      description: 'Replace Falco\'s blaster gun model',
      targetFile: 'PlFc.dat',
      icon: 'gun',
      type: 'model',  // Model type - uses .dae file instead of hex patches
      modelPath: 'ftDataFalco/Articles/Articles_1/Model_/RootModelJoint'
    }
  ],
  Fox: [
    {
      id: 'laser',
      name: 'Laser Color',
      description: 'Change laser beam colors',
      targetFile: 'PlFx.dat',
      icon: 'laser',
      // Offset definitions for the 98 matrix format (Fox-specific)
      offsets: {
        wide: { start: 0x13E20, end: 0x13E80 },
        thin: { start: 0x13EC0, end: 0x13F20 },
        outline: { start: 0x13F60, end: 0x13FC0 }
      },
      properties: [
        { id: 'wide', name: 'Wide Layer', description: 'Transparent outer glow' },
        { id: 'thin', name: 'Thin Layer', description: 'Semi-transparent middle' },
        { id: 'outline', name: 'Outline', description: 'Opaque inner core' }
      ]
    },
    {
      id: 'sideb',
      name: 'Side-B Color',
      description: 'Illusion afterimage colors',
      targetFile: 'PlFx.dat',
      icon: 'sideb',
      format: '42_48',
      // 42_48 format: 3 RGBA colors
      offsets: {
        primary: { start: 0x2204C, size: 4 },
        secondary: { start: 0x22050, size: 4 },
        tertiary: { start: 0x22054, size: 4 }
      },
      vanilla: {
        primary: '0099FFFF',
        secondary: 'CCE6FFFF',
        tertiary: 'FFFFFFFF'
      },
      properties: [
        { id: 'primary', name: 'Primary', description: 'Main afterimage color' },
        { id: 'secondary', name: 'Secondary', description: 'Edge/gradient color' },
        { id: 'tertiary', name: 'Glow', description: 'Outer glow color' }
      ]
    },
    {
      id: 'upb',
      name: 'Up-B Color',
      description: 'Firefox/Firebird flame colors',
      targetFile: 'EfFxData.dat',
      icon: 'upb',
      shared: true,  // Shared between Fox and Falco
      sharedWith: ['Falco'],  // Characters that share this extra
      owner: 'Fox',  // Which character owns the mods in storage
      offsets: {
        // 98 matrix format for flame tip
        tip: { start: 0x1AC80, end: 0x1AD00, format: 'RGBY' },
        // 98 matrix format for firefox body when not textured
        body: { start: 0x1A880, end: 0x1AA50, format: 'RGB' },
        // CF format - trailing fire (all sizes combined)
        // CF XX RR GG BB - color at offset+2
        trail: {
          format: 'CF',
          offsets: [
            0x2EE, 0x2F4, 0x324, 0x32B,  // Large trailing fire
            0x52E, 0x534  // Big trailing fire
          ]
        },
        // 070707 format - fire rings
        // 07 07 07 04 RR GG BB 00 RR GG BB - colors at +4 and +8
        rings: {
          format: '070707',
          offsets: [0x1B454, 0x1B520]
        }
      },
      vanilla: {
        tip: 'FE60',      // Fire orange (RGBY)
        body: 'FFFFFF',   // White (RGB)
        trail: 'FFFFFF',  // White (RGB)
        rings: 'FFFF00'   // Yellow (RGB)
      },
      properties: [
        { id: 'tip', name: 'Flame Tip', description: 'Fire effect at the tip', format: 'RGBY' },
        { id: 'body', name: 'Body Glow', description: 'Firefox body when charging', format: 'RGB' },
        { id: 'trail', name: 'Trail Fire', description: 'Trailing fire particles', format: 'RGB' },
        { id: 'rings', name: 'Fire Rings', description: 'Circular fire rings', format: 'RGB' }
      ]
    },
    {
      id: 'shine',
      name: 'Shine Color',
      description: 'Reflector shield colors',
      targetFile: 'EfFxData.dat',
      icon: 'shine',
      shared: true,  // Shared between Fox and Falco
      sharedWith: ['Falco'],  // Characters that share this extra
      owner: 'Fox',  // Which character owns the mods in storage
      offsets: {
        // 98 matrix format for main hexagon shape
        hex: { start: 0x1C2A0, end: 0x1C350, format: 'RGBY' },
        // 98 matrix format for inner glow
        inner: { start: 0x1C860, end: 0x1C8D0, format: 'RGBY' },
        // 98 matrix format for outer glow (multiple matrices, same color)
        outer: {
          format: '98_multi',
          ranges: [
            { start: 0x1C8E0, end: 0x1C920 },
            { start: 0x1C91F, end: 0x1C960 },
            { start: 0x1C95E, end: 0x1C9A0 }
          ]
        },
        // 42_48 format for transparent bubble
        bubble: { start: 0x1B4C4, format: '42_48', size: 12 }
      },
      vanilla: {
        hex: '621F',       // Blue-ish (RGBY)
        inner: '63FF',     // Blue (RGBY)
        outer: '63FF',     // Blue (RGBY)
        bubble: '808080FFFFFFFFFFFFFFFFFF'  // Gray/white gradient (3x RGBA)
      },
      properties: [
        { id: 'hex', name: 'Hexagon', description: 'Main shield shape', format: 'RGBY' },
        { id: 'inner', name: 'Inner Glow', description: 'Inner glow effect', format: 'RGBY' },
        { id: 'outer', name: 'Outer Glow', description: 'Outer flash effect', format: 'RGBY' },
        { id: 'bubble', name: 'Bubble', description: 'Transparent bubble overlay', format: '42_48' }
      ]
    },
    {
      id: 'gun',
      name: 'Gun Model',
      description: 'Replace Fox\'s blaster gun model',
      targetFile: 'PlFx.dat',
      icon: 'gun',
      type: 'model',  // Model type - uses .dae file instead of hex patches
      modelPath: 'ftDataFox/Articles/Articles_1/Model_/RootModelJoint'
    }
  ]
}

/**
 * Check if a character has any extras available (including shared)
 * @param {string} character - Character name
 * @returns {boolean}
 */
export function hasExtras(character) {
  if (EXTRA_TYPES[character]?.length > 0) {
    return true
  }
  // Check if any other character has shared extras for this character
  for (const [otherChar, extras] of Object.entries(EXTRA_TYPES)) {
    for (const extra of extras) {
      if (extra.shared && extra.sharedWith?.includes(character)) {
        return true
      }
    }
  }
  return false
}

/**
 * Get all extra types for a character, including shared extras from other characters
 * @param {string} character - Character name
 * @returns {Array}
 */
export function getExtraTypes(character) {
  // Start with the character's own extras
  const result = [...(EXTRA_TYPES[character] || [])]

  // Add shared extras from other characters
  for (const [otherChar, extras] of Object.entries(EXTRA_TYPES)) {
    if (otherChar === character) continue
    for (const extra of extras) {
      if (extra.shared && extra.sharedWith?.includes(character)) {
        // Include the shared extra (it's already configured with owner info)
        result.push(extra)
      }
    }
  }

  return result
}

/**
 * Get a specific extra type by id (including shared extras)
 * @param {string} character - Character name
 * @param {string} typeId - Extra type id (e.g., 'laser')
 * @returns {Object|null}
 */
export function getExtraType(character, typeId) {
  // Use getExtraTypes which includes shared extras
  const types = getExtraTypes(character)
  return types.find(t => t.id === typeId) || null
}

/**
 * Get the character to use for storage (owner for shared extras)
 * @param {string} character - Character name
 * @param {string} typeId - Extra type id
 * @returns {string}
 */
export function getStorageCharacter(character, typeId) {
  const typeConfig = getExtraType(character, typeId)
  if (typeConfig?.shared) {
    return typeConfig.owner || character
  }
  return character
}
