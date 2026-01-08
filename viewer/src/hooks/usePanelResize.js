import { useState, useCallback, useEffect } from 'react'

const STORAGE_KEY = 'skinCreatorPanelSizes'

const DEFAULT_SIZES = {
  rightPanelWidth: 350,
  textureStripHeight: 220,
  previewHeightRatio: 0.5,
}

const CONSTRAINTS = {
  rightPanelWidth: { min: 250, max: 700 },
  textureStripHeight: { min: 100, max: 500 },
  previewHeightRatio: { min: 0.2, max: 0.8 },
}

export function usePanelResize() {
  const [sizes, setSizes] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        return { ...DEFAULT_SIZES, ...parsed }
      }
    } catch (e) {
      // Ignore parse errors
    }
    return DEFAULT_SIZES
  })

  // Save to localStorage when sizes change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sizes))
    } catch (e) {
      // Ignore storage errors
    }
  }, [sizes])

  // Right panel width resize (vertical divider, drag left/right)
  const handleRightPanelResize = useCallback((e) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = sizes.rightPanelWidth

    const handleMove = (moveEvent) => {
      const delta = startX - moveEvent.clientX
      const newWidth = Math.max(
        CONSTRAINTS.rightPanelWidth.min,
        Math.min(CONSTRAINTS.rightPanelWidth.max, startWidth + delta)
      )
      setSizes(prev => ({ ...prev, rightPanelWidth: newWidth }))
    }

    const handleEnd = () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.body.style.cursor = 'ew-resize'
    document.body.style.userSelect = 'none'
  }, [sizes.rightPanelWidth])

  // Texture strip height resize (horizontal divider, drag up/down)
  const handleTextureStripResize = useCallback((e) => {
    e.preventDefault()
    const startY = e.clientY
    const startHeight = sizes.textureStripHeight

    const handleMove = (moveEvent) => {
      const delta = startY - moveEvent.clientY
      const newHeight = Math.max(
        CONSTRAINTS.textureStripHeight.min,
        Math.min(CONSTRAINTS.textureStripHeight.max, startHeight + delta)
      )
      setSizes(prev => ({ ...prev, textureStripHeight: newHeight }))
    }

    const handleEnd = () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.body.style.cursor = 'ns-resize'
    document.body.style.userSelect = 'none'
  }, [sizes.textureStripHeight])

  // Preview/tool palette ratio resize (horizontal divider within right panel)
  const handlePreviewResize = useCallback((e) => {
    e.preventDefault()
    const startY = e.clientY
    const rightPanel = e.target.closest('.skin-creator-right-panel')
    if (!rightPanel) return

    const panelRect = rightPanel.getBoundingClientRect()
    const panelHeight = panelRect.height

    const handleMove = (moveEvent) => {
      const relativeY = moveEvent.clientY - panelRect.top
      const newRatio = Math.max(
        CONSTRAINTS.previewHeightRatio.min,
        Math.min(CONSTRAINTS.previewHeightRatio.max, relativeY / panelHeight)
      )
      setSizes(prev => ({ ...prev, previewHeightRatio: newRatio }))
    }

    const handleEnd = () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.body.style.cursor = 'ns-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const resetSizes = useCallback(() => {
    setSizes(DEFAULT_SIZES)
  }, [])

  return {
    sizes,
    handleRightPanelResize,
    handleTextureStripResize,
    handlePreviewResize,
    resetSizes,
  }
}
