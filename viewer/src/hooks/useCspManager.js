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
    // Load alternate CSPs from skin data if available
    const alts = (skinData.alternateCsps || []).map(alt => ({
      id: alt.id,
      url: alt.url,
      poseName: alt.poseName,
      isHd: alt.isHd,
      timestamp: alt.timestamp,
      file: null // Not a new file, loaded from server
    }))
    setAlternativeCsps(alts)
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

  // Add alternative CSP - upload to backend
  const handleAddAlternativeCsp = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    try {
      const formData = new FormData()
      formData.append('action', 'add')
      formData.append('file', file)

      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        { method: 'POST', body: formData }
      )

      const data = await response.json()

      if (data.success) {
        // Add to local state with URL from server
        setAlternativeCsps(prev => [...prev, {
          id: data.altId,
          url: data.url,
          poseName: null,
          isHd: false,
          file: null
        }])
        setLastImageUpdate(Date.now())
      } else {
        alert(`Failed to add CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error adding CSP: ${err.message}`)
    }
  }

  // Swap CSP with alternative - call backend
  const handleSwapCsp = async (altIndex) => {
    const altCsp = alternativeCsps[altIndex]
    if (!altCsp) return

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'swap', altId: altCsp.id })
        }
      )

      const data = await response.json()

      if (data.success) {
        // Bust image cache and refresh
        setLastImageUpdate(Date.now())
        // Refresh metadata to get updated CSP data
        if (onRefresh) {
          onRefresh()
        }
        // Update local state: remove swapped alt, add new alt (old main) if provided
        setAlternativeCsps(prev => {
          const updated = prev.filter(a => a.id !== altCsp.id)
          if (data.newAltId) {
            updated.push({
              id: data.newAltId,
              url: `${cspManagerSkin.cspUrl}?t=${Date.now()}`, // Old main is now alt
              poseName: null,
              isHd: false,
              file: null
            })
          }
          return updated
        })
      } else {
        alert(`Failed to swap CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error swapping CSP: ${err.message}`)
    }
  }

  // Remove alternative CSP - call backend
  const handleRemoveAlternativeCsp = async (altIndex) => {
    const altCsp = alternativeCsps[altIndex]
    if (!altCsp) return

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'remove', altId: altCsp.id })
        }
      )

      const data = await response.json()

      if (data.success) {
        // Remove from local state
        setAlternativeCsps(prev => prev.filter((_, i) => i !== altIndex))
      } else {
        alert(`Failed to remove CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error removing CSP: ${err.message}`)
    }
  }

  // Save CSP manager changes - upload pending main CSP if any
  const handleSaveCspManager = async () => {
    try {
      if (pendingMainCsp) {
        // Upload new main CSP using existing endpoint
        const formData = new FormData()
        formData.append('character', cspManagerSkin.character)
        formData.append('skinId', cspManagerSkin.id)
        formData.append('csp', pendingMainCsp)

        const response = await fetch(`${API_URL}/storage/costumes/update-csp`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()

        if (!data.success) {
          alert(`Failed to save CSP: ${data.error}`)
          return
        }
      }

      // Refresh metadata
      if (onRefresh) {
        onRefresh()
      }

      closeCspManager()
    } catch (err) {
      alert(`Error saving CSP: ${err.message}`)
    }
  }

  // Regenerate alt CSP at HD resolution using its pose (or default)
  const handleRegenerateAltHd = async (altIndex) => {
    const altCsp = alternativeCsps[altIndex]
    if (!altCsp) return

    const scaleNum = parseInt(hdResolution.replace('x', ''))

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'regenerate-hd',
            altId: altCsp.id,
            scale: scaleNum
          })
        }
      )

      const data = await response.json()

      if (data.success) {
        // Update local state to show HD badge
        setAlternativeCsps(prev => prev.map((alt, i) =>
          i === altIndex ? { ...alt, isHd: true } : alt
        ))
        setLastImageUpdate(Date.now())
      } else {
        alert(`Failed to regenerate HD: ${data.error}`)
      }
    } catch (err) {
      alert(`Error regenerating HD: ${err.message}`)
    }
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
    handleCaptureHdCsp,
    handleRegenerateAltHd
  }
}
