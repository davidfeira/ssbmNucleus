import { useState, useEffect, useRef } from 'react'
import { analyzeTextureColors, applyGroupAdjustments } from './colorUtils'

// Color palette analysis and batch hue/saturation adjustments across all textures.
export function useColorPalette({ modelTextures, editedTextures, setEditedTextures, setIsDirty, hasElectron, viewerWs }) {
  const [colorPaletteEnabled, setColorPaletteEnabled] = useState(false)
  const [colorGroups, setColorGroups] = useState([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [maxColorGroups, setMaxColorGroups] = useState(8)
  const [selectedColorGroup, setSelectedColorGroup] = useState(null)
  const [originalTextureData, setOriginalTextureData] = useState({}) // { [index]: ImageData }
  const pixelGroupMapRef = useRef({}) // Maps pixels to their color group index
  const colorDebounceRef = useRef(null)

  // Analyze all textures and detect color groups
  const analyzeColors = async () => {
    if (modelTextures.length === 0) return
    setIsAnalyzing(true)

    try {
      // First, capture original texture data
      const originals = {}
      for (let texIdx = 0; texIdx < modelTextures.length; texIdx++) {
        const tex = modelTextures[texIdx]
        const imgSrc = editedTextures[texIdx] || (tex.thumbnail ? `data:image/png;base64,${tex.thumbnail}` : null)
        if (!imgSrc) continue

        const img = await new Promise((resolve) => {
          const i = new Image()
          i.onload = () => resolve(i)
          i.src = imgSrc
        })

        const canvas = document.createElement('canvas')
        canvas.width = tex.width
        canvas.height = tex.height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, tex.width, tex.height)
        originals[texIdx] = ctx.getImageData(0, 0, tex.width, tex.height)
      }
      setOriginalTextureData(originals)

      const { groups, pixelMap } = analyzeTextureColors(originals, maxColorGroups)
      pixelGroupMapRef.current = pixelMap

      setColorGroups(groups)
      setColorPaletteEnabled(true)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Apply color adjustments to all textures
  const applyColorAdjustments = (groups) => {
    if (!groups || groups.length === 0 || Object.keys(originalTextureData).length === 0) return

    // Skip if all adjustments are zero
    const hasAdjustments = groups.some(g => g.hueShift !== 0 || g.saturationShift !== 0)
    if (!hasAdjustments) return

    const newEditedTextures = { ...editedTextures }

    for (const texIdxStr of Object.keys(originalTextureData)) {
      const texIdx = parseInt(texIdxStr)
      const original = originalTextureData[texIdx]
      const pixelMap = pixelGroupMapRef.current[texIdx]
      if (!original || !pixelMap) continue

      const result = applyGroupAdjustments(original, pixelMap, groups)

      // Convert to data URL
      const canvas = document.createElement('canvas')
      canvas.width = original.width
      canvas.height = original.height
      const ctx = canvas.getContext('2d')
      ctx.putImageData(result, 0, 0)
      newEditedTextures[texIdx] = canvas.toDataURL('image/png')

      // Send to viewer via Electron IPC
      if (hasElectron && viewerWs) {
        const base64 = newEditedTextures[texIdx].replace('data:image/png;base64,', '')
        window.electron.viewerSend({
          type: 'updateTexture',
          index: texIdx,
          data: base64
        })
      }
    }

    setEditedTextures(newEditedTextures)
    setIsDirty(true)
  }

  // Handle color group adjustment
  const handleColorAdjust = (groupId, field, value) => {
    setColorGroups(prev => prev.map(g => {
      if (g.id !== groupId) return g
      if (field === 'reset') {
        return { ...g, hueShift: 0, saturationShift: 0 }
      }
      return { ...g, [field]: value }
    }))
  }

  // Apply color adjustments when groups change (debounced via effect)
  useEffect(() => {
    if (!colorPaletteEnabled || colorGroups.length === 0) return

    // Debounce the application
    if (colorDebounceRef.current) {
      clearTimeout(colorDebounceRef.current)
    }
    colorDebounceRef.current = setTimeout(() => {
      applyColorAdjustments(colorGroups)
    }, 50)

    return () => {
      if (colorDebounceRef.current) {
        clearTimeout(colorDebounceRef.current)
      }
    }
  }, [colorGroups, colorPaletteEnabled])

  // Reset color palette
  const resetColorPalette = () => {
    setColorPaletteEnabled(false)
    setColorGroups([])
    setSelectedColorGroup(null)
    setOriginalTextureData({})
    pixelGroupMapRef.current = {}
  }

  // Reset palette state when the skin creator closes (does not touch selectedColorGroup,
  // matching the original close behavior)
  const clearPaletteState = () => {
    setColorPaletteEnabled(false)
    setColorGroups([])
    setOriginalTextureData({})
    pixelGroupMapRef.current = {}
  }

  return {
    colorPaletteEnabled,
    colorGroups,
    isAnalyzing,
    maxColorGroups,
    setMaxColorGroups,
    selectedColorGroup,
    setSelectedColorGroup,
    analyzeColors,
    resetColorPalette,
    clearPaletteState,
    handleColorAdjust
  }
}
