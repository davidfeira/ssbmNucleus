/**
 * Color utility functions for RGB, HSL, and HEX conversions
 */

/**
 * Convert RGB to HEX
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {string} HEX color string (e.g., "#ff0000")
 */
export function rgbToHex(r, g, b) {
  const toHex = (n) => {
    const hex = Math.round(Math.max(0, Math.min(255, n))).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

/**
 * Convert HEX to RGB
 * @param {string} hex - HEX color string (e.g., "#ff0000" or "ff0000")
 * @returns {Object} RGB object with r, g, b properties
 */
export function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

/**
 * Convert RGB to HSL
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {Object} HSL object with h (0-360), s (0-100), l (0-100)
 */
export function rgbToHsl(r, g, b) {
  r /= 255
  g /= 255
  b /= 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s
  const l = (max + min) / 2

  if (max === min) {
    h = s = 0 // achromatic
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6
        break
      case g:
        h = ((b - r) / d + 2) / 6
        break
      case b:
        h = ((r - g) / d + 4) / 6
        break
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  }
}

/**
 * Convert HSL to RGB
 * @param {number} h - Hue (0-360)
 * @param {number} s - Saturation (0-100)
 * @param {number} l - Lightness (0-100)
 * @returns {Object} RGB object with r, g, b properties
 */
export function hslToRgb(h, s, l) {
  h /= 360
  s /= 100
  l /= 100

  let r, g, b

  if (s === 0) {
    r = g = b = l // achromatic
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1
      if (t > 1) t -= 1
      if (t < 1/6) return p + (q - p) * 6 * t
      if (t < 1/2) return q
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
      return p
    }

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q

    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
  }

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255)
  }
}

/**
 * Calculate luminance of a color (0-1)
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {number} Luminance value (0-1)
 */
export function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

/**
 * Calculate contrast ratio between two colors
 * @param {number} r1 - Red of first color
 * @param {number} g1 - Green of first color
 * @param {number} b1 - Blue of first color
 * @param {number} r2 - Red of second color
 * @param {number} g2 - Green of second color
 * @param {number} b2 - Blue of second color
 * @returns {number} Contrast ratio (1-21)
 */
export function getContrastRatio(r1, g1, b1, r2, g2, b2) {
  const l1 = getLuminance(r1, g1, b1)
  const l2 = getLuminance(r2, g2, b2)
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * Darken a color by a percentage
 * @param {string} hex - HEX color string
 * @param {number} percent - Percentage to darken (0-100)
 * @returns {string} Darkened HEX color
 */
export function darkenColor(hex, percent) {
  const rgb = hexToRgb(hex)
  if (!rgb) return hex

  const factor = 1 - (percent / 100)
  const r = Math.round(rgb.r * factor)
  const g = Math.round(rgb.g * factor)
  const b = Math.round(rgb.b * factor)

  return rgbToHex(r, g, b)
}

/**
 * Lighten a color by a percentage
 * @param {string} hex - HEX color string
 * @param {number} percent - Percentage to lighten (0-100)
 * @returns {string} Lightened HEX color
 */
export function lightenColor(hex, percent) {
  const rgb = hexToRgb(hex)
  if (!rgb) return hex

  const factor = percent / 100
  const r = Math.round(rgb.r + (255 - rgb.r) * factor)
  const g = Math.round(rgb.g + (255 - rgb.g) * factor)
  const b = Math.round(rgb.b + (255 - rgb.b) * factor)

  return rgbToHex(r, g, b)
}

/**
 * Check if a color is considered "dark"
 * @param {number} r - Red (0-255)
 * @param {number} g - Green (0-255)
 * @param {number} b - Blue (0-255)
 * @returns {boolean} True if color is dark
 */
export function isDark(r, g, b) {
  const luminance = getLuminance(r, g, b)
  return luminance < 0.5
}
