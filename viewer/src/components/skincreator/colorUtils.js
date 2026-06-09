// Color utility functions and palette analysis (pure, no React state)

export const rgbToHsl = (r, g, b) => {
  r /= 255; g /= 255; b /= 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s, l = (max + min) / 2

  if (max === min) {
    h = s = 0
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
      default: h = 0
    }
  }
  return { h: h * 360, s: s * 100, l: l * 100 }
}

export const hslToRgb = (h, s, l) => {
  h /= 360; s /= 100; l /= 100
  let r, g, b

  if (s === 0) {
    r = g = b = l
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

// Analyze captured texture ImageData and detect color groups.
// originals: { [texIdx]: ImageData }
// Returns { groups, pixelMap } where pixelMap maps pixels to their color group index per texture.
export const analyzeTextureColors = (originals, maxColorGroups) => {
  // Collect all pixels with their HSL values
  const HUE_TOLERANCE = 25
  const hueBins = new Array(360).fill(null).map(() => ({ count: 0, totalS: 0, totalL: 0 }))

  for (const texIdx of Object.keys(originals)) {
    const imageData = originals[texIdx]
    const { data } = imageData

    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3]
      if (a < 128) continue // Skip transparent

      const hsl = rgbToHsl(r, g, b)
      if (hsl.l < 10 || hsl.l > 90) continue // Skip near black/white
      if (hsl.s < 15) continue // Skip grays

      const hueIdx = Math.floor(hsl.h) % 360
      hueBins[hueIdx].count++
      hueBins[hueIdx].totalS += hsl.s
      hueBins[hueIdx].totalL += hsl.l
    }
  }

  // Merge adjacent hue bins into groups
  const rawGroups = []
  let currentGroup = null

  for (let h = 0; h < 360; h++) {
    const bin = hueBins[h]
    if (bin.count > 0) {
      if (!currentGroup) {
        currentGroup = { startHue: h, endHue: h, count: bin.count, totalS: bin.totalS, totalL: bin.totalL }
      } else if (h - currentGroup.endHue <= HUE_TOLERANCE) {
        currentGroup.endHue = h
        currentGroup.count += bin.count
        currentGroup.totalS += bin.totalS
        currentGroup.totalL += bin.totalL
      } else {
        if (currentGroup.count >= 100) rawGroups.push(currentGroup)
        currentGroup = { startHue: h, endHue: h, count: bin.count, totalS: bin.totalS, totalL: bin.totalL }
      }
    }
  }
  if (currentGroup && currentGroup.count >= 100) rawGroups.push(currentGroup)

  // Handle wrap-around (red at 0 and 360)
  if (rawGroups.length >= 2) {
    const first = rawGroups[0]
    const last = rawGroups[rawGroups.length - 1]
    if (first.startHue < HUE_TOLERANCE && last.endHue > 360 - HUE_TOLERANCE) {
      // Merge last into first
      first.startHue = last.startHue - 360
      first.count += last.count
      first.totalS += last.totalS
      first.totalL += last.totalL
      rawGroups.pop()
    }
  }

  // Adjust groups to exactly match maxColorGroups
  // Merge if too many, split if too few

  // Merge closest groups if we have too many
  while (rawGroups.length > maxColorGroups) {
    let minDist = Infinity
    let mergeI = 0, mergeJ = 1

    for (let i = 0; i < rawGroups.length; i++) {
      for (let j = i + 1; j < rawGroups.length; j++) {
        const g1 = rawGroups[i]
        const g2 = rawGroups[j]
        const hue1 = ((g1.startHue + g1.endHue) / 2 + 360) % 360
        const hue2 = ((g2.startHue + g2.endHue) / 2 + 360) % 360
        let dist = Math.abs(hue1 - hue2)
        if (dist > 180) dist = 360 - dist
        if (dist < minDist) {
          minDist = dist
          mergeI = i
          mergeJ = j
        }
      }
    }

    const gi = rawGroups[mergeI]
    const gj = rawGroups[mergeJ]
    gi.startHue = Math.min(gi.startHue, gj.startHue)
    gi.endHue = Math.max(gi.endHue, gj.endHue)
    gi.count += gj.count
    gi.totalS += gj.totalS
    gi.totalL += gj.totalL
    rawGroups.splice(mergeJ, 1)
  }

  // Split largest groups if we have too few
  while (rawGroups.length < maxColorGroups && rawGroups.length > 0) {
    // Find the group with the widest hue range to split
    let maxRange = -1
    let splitIdx = 0
    for (let i = 0; i < rawGroups.length; i++) {
      const g = rawGroups[i]
      const range = g.endHue - g.startHue
      if (range > maxRange) {
        maxRange = range
        splitIdx = i
      }
    }

    const g = rawGroups[splitIdx]
    if (g.endHue - g.startHue < 2) {
      // Can't split further, just duplicate with slight offset
      break
    }

    const midHue = Math.floor((g.startHue + g.endHue) / 2)

    // Create two new groups from the split
    const g1 = {
      startHue: g.startHue,
      endHue: midHue,
      count: Math.floor(g.count / 2),
      totalS: g.totalS / 2,
      totalL: g.totalL / 2
    }
    const g2 = {
      startHue: midHue + 1,
      endHue: g.endHue,
      count: Math.ceil(g.count / 2),
      totalS: g.totalS / 2,
      totalL: g.totalL / 2
    }

    rawGroups.splice(splitIdx, 1, g1, g2)
  }

  // Sort by pixel count for consistent ordering
  rawGroups.sort((a, b) => b.count - a.count)

  // Convert to color group objects
  const groups = rawGroups.map((g, idx) => {
    const avgS = g.totalS / g.count
    const avgL = g.totalL / g.count
    const centerHue = ((g.startHue + g.endHue) / 2 + 360) % 360
    return {
      id: `group-${idx}`,
      centerHue,
      hueRange: [(g.startHue + 360) % 360, g.endHue % 360],
      pixelCount: g.count,
      displayColor: `hsl(${Math.round(centerHue)}, ${Math.round(avgS)}%, ${Math.round(avgL)}%)`,
      avgSaturation: avgS,
      avgLightness: avgL,
      hueShift: 0,
      saturationShift: 0
    }
  })

  // Build pixel-to-group map for each texture
  const pixelMap = {}
  for (const texIdx of Object.keys(originals)) {
    const imageData = originals[texIdx]
    const { data, width, height } = imageData
    const map = new Uint8Array(width * height).fill(255)

    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3]
      if (a < 128) continue

      const hsl = rgbToHsl(r, g, b)
      if (hsl.l < 10 || hsl.l > 90) continue
      if (hsl.s < 15) continue

      const pixelHue = hsl.h
      for (let gIdx = 0; gIdx < groups.length; gIdx++) {
        const group = groups[gIdx]
        let inRange = false
        if (group.hueRange[0] <= group.hueRange[1]) {
          inRange = pixelHue >= group.hueRange[0] - HUE_TOLERANCE && pixelHue <= group.hueRange[1] + HUE_TOLERANCE
        } else {
          // Wraps around 0
          inRange = pixelHue >= group.hueRange[0] - HUE_TOLERANCE || pixelHue <= group.hueRange[1] + HUE_TOLERANCE
        }
        if (inRange) {
          map[i / 4] = gIdx
          break
        }
      }
    }
    pixelMap[texIdx] = map
  }

  return { groups, pixelMap }
}

// Apply hue/saturation shifts of color groups to a single texture's original ImageData.
// Returns a new ImageData with the adjustments applied.
export const applyGroupAdjustments = (original, pixelMap, groups) => {
  const result = new ImageData(
    new Uint8ClampedArray(original.data),
    original.width,
    original.height
  )

  for (let i = 0; i < result.data.length; i += 4) {
    const pixelIdx = i / 4
    const groupIdx = pixelMap[pixelIdx]
    if (groupIdx === 255) continue

    const group = groups[groupIdx]
    if (!group || (group.hueShift === 0 && group.saturationShift === 0)) continue

    const r = original.data[i]
    const g = original.data[i + 1]
    const b = original.data[i + 2]

    const hsl = rgbToHsl(r, g, b)
    let newH = (hsl.h + group.hueShift + 360) % 360
    let newS = Math.max(0, Math.min(100, hsl.s + group.saturationShift))

    const newRgb = hslToRgb(newH, newS, hsl.l)
    result.data[i] = newRgb.r
    result.data[i + 1] = newRgb.g
    result.data[i + 2] = newRgb.b
  }

  return result
}
