/**
 * useCspManager Hook
 *
 * Manages CSP (Character Select Portrait) manager functionality including:
 * - Opening/closing CSP manager modal
 * - Managing alternative CSPs
 * - Swapping CSPs
 * - HD CSP capture
 * - Before/after comparison slider
 */

import { useState } from 'react'

export function useCspManager({ API_URL, onRefresh }) {
  // CSP Manager modal state
  const [showCspManager, setShowCspManager] = useState(false)
  const [cspManagerSkin, setCspManagerSkin] = useState(null) // Current skin being edited
  const [alternativeCsps, setAlternativeCsps] = useState([]) // Array of { id, url, file }
  const [pendingMainCsp, setPendingMainCsp] = useState(null) // New main CSP file pending save
  const [pendingMainCspPreview, setPendingMainCspPreview] = useState(null) // Preview URL
  const [hdResolution, setHdResolution] = useState('4x') // '2x' | '4x' | '8x' | '16x'
  const [hdCspInfo, setHdCspInfo] = useState(null) // { exists: bool, resolution: '4x', size: '1024x1365' }
  const [compareSliderPosition, setCompareSliderPosition] = useState(50) // 0-100% for before/after slider
  const [lastImageUpdate, setLastImageUpdate] = useState(Date.now()) // For cache-busting images
  const [capturingHdCsp, setCapturingHdCsp] = useState(false)

  // Open CSP manager
  const openCspManager = (skinData) => {
    setCspManagerSkin(skinData)
    setAlternativeCsps([])
    setPendingMainCsp(null)
    setPendingMainCspPreview(null)
    setHdResolution('4x')
    setCompareSliderPosition(50) // Reset slider to middle
    if (skinData.has_hd_csp) {
      setHdCspInfo({
        exists: true,
        resolution: skinData.hd_csp_resolution,
        size: skinData.hd_csp_size
      })
    } else {
      setHdCspInfo(null)
    }
    setShowCspManager(true)
  }

  // Close CSP manager
  const closeCspManager = () => {
    setShowCspManager(false)
    setCspManagerSkin(null)
    setAlternativeCsps([])
    setPendingMainCsp(null)
    setPendingMainCspPreview(null)
    setCompareSliderPosition(50) // Reset slider position
  }

  // Handle comparison slider drag
  const handleCompareSliderStart = (e) => {
    e.preventDefault()
    const handleMove = (moveEvent) => {
      const container = e.target.closest('.csp-manager-main-container')
      if (!container) return
      const rect = container.getBoundingClientRect()
      const x = (moveEvent.clientX || moveEvent.touches?.[0]?.clientX) - rect.left
      const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
      setCompareSliderPosition(percentage)
    }

    const handleEnd = () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.removeEventListener('touchmove', handleMove)
      document.removeEventListener('touchend', handleEnd)
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.addEventListener('touchmove', handleMove)
    document.addEventListener('touchend', handleEnd)
  }

  // Handle main CSP change
  const handleCspManagerMainChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    setPendingMainCsp(file)
    const reader = new FileReader()
    reader.onload = (e) => setPendingMainCspPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  // Add alternative CSP
  const handleAddAlternativeCsp = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => {
      const newAlt = {
        id: `alt_${Date.now()}`,
        url: ev.target.result,
        file: file
      }
      setAlternativeCsps(prev => [...prev, newAlt])
    }
    reader.readAsDataURL(file)
  }

  // Swap CSP with alternative
  const handleSwapCsp = (altIndex) => {
    const altCsp = alternativeCsps[altIndex]
    if (!altCsp) return

    // Get current main CSP info
    const currentMainUrl = pendingMainCspPreview ||
      (cspManagerSkin?.has_csp ? `${cspManagerSkin.cspUrl}?t=${lastImageUpdate}` : null)
    const currentMainFile = pendingMainCsp

    // Swap: alt becomes main, main becomes alt
    setPendingMainCspPreview(altCsp.url)
    setPendingMainCsp(altCsp.file)

    // Update alternatives: replace swapped alt with old main
    setAlternativeCsps(prev => {
      const updated = [...prev]
      if (currentMainUrl) {
        updated[altIndex] = {
          id: `alt_${Date.now()}`,
          url: currentMainUrl,
          file: currentMainFile
        }
      } else {
        // No main CSP existed, just remove the alt
        updated.splice(altIndex, 1)
      }
      return updated
    })
  }

  // Remove alternative CSP
  const handleRemoveAlternativeCsp = (altIndex) => {
    setAlternativeCsps(prev => prev.filter((_, i) => i !== altIndex))
  }

  // Save CSP manager changes
  const handleSaveCspManager = () => {
    // TODO: Implement backend save
    // For now, just close the modal
    closeCspManager()
  }

  // Capture HD CSP
  const handleCaptureHdCsp = async () => {
    if (!cspManagerSkin) return

    const scaleNum = parseInt(hdResolution.replace('x', ''))
    setCapturingHdCsp(true)

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/capture-hd`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scale: scaleNum })
        }
      )

      const data = await response.json()

      if (data.success) {
        setHdCspInfo({
          exists: true,
          resolution: data.resolution,
          size: data.size
        })
        // Bust image cache so the new HD CSP shows immediately
        setLastImageUpdate(Date.now())
        // Refresh metadata to get updated has_hd_csp flag
        if (onRefresh) {
          onRefresh()
        }
      } else {
        alert(`Failed to capture HD CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error capturing HD CSP: ${err.message}`)
    } finally {
      setCapturingHdCsp(false)
    }
  }

  return {
    // State
    showCspManager,
    setShowCspManager,
    cspManagerSkin,
    setCspManagerSkin,
    alternativeCsps,
    setAlternativeCsps,
    pendingMainCsp,
    setPendingMainCsp,
    pendingMainCspPreview,
    setPendingMainCspPreview,
    hdResolution,
    setHdResolution,
    hdCspInfo,
    setHdCspInfo,
    compareSliderPosition,
    setCompareSliderPosition,
    lastImageUpdate,
    setLastImageUpdate,
    capturingHdCsp,

    // Handlers
    openCspManager,
    closeCspManager,
    handleCompareSliderStart,
    handleCspManagerMainChange,
    handleAddAlternativeCsp,
    handleSwapCsp,
    handleRemoveAlternativeCsp,
    handleSaveCspManager,
    handleCaptureHdCsp
  }
}
