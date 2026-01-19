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

export function useCspManager({ API_URL, onRefresh, onUpdateEditingItemAlts, onUpdateEditingItemActiveCsp }) {
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
        const newAlt = {
          id: data.altId,
          url: data.url,
          poseName: null,
          isHd: false,
          file: null
        }
        // Add to local state with URL from server
        setAlternativeCsps(prev => [...prev, newAlt])
        // Update editingItem so reopening CSP Manager shows fresh data
        if (onUpdateEditingItemAlts) {
          onUpdateEditingItemAlts(prev => [...prev, newAlt])
        }
        setLastImageUpdate(Date.now())
        // Refresh parent metadata so changes persist after modal close/reopen
        if (onRefresh) {
          onRefresh()
        }
      } else {
        alert(`Failed to add CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error adding CSP: ${err.message}`)
    }
  }

  // Swap CSP - just updates active_csp_id flag, no file moves
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
        // Bust image cache and refresh metadata
        setLastImageUpdate(Date.now())
        if (onRefresh) {
          onRefresh()
        }
        // Update local skin data with new active CSP
        setCspManagerSkin(prev => ({
          ...prev,
          active_csp_id: data.activeCspId
        }))
        // Update editingItem so Edit Modal shows new active CSP immediately
        if (onUpdateEditingItemActiveCsp) {
          onUpdateEditingItemActiveCsp(data.activeCspId)
        }
      } else {
        alert(`Failed to set active CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error setting active CSP: ${err.message}`)
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
        const removedId = alternativeCsps[altIndex]?.id
        // Remove from local state
        setAlternativeCsps(prev => prev.filter((_, i) => i !== altIndex))
        // Update editingItem so reopening CSP Manager shows fresh data
        if (onUpdateEditingItemAlts && removedId) {
          onUpdateEditingItemAlts(prev => prev.filter(a => a.id !== removedId))
        }
        // Refresh parent metadata so changes persist after modal close/reopen
        if (onRefresh) {
          onRefresh()
        }
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

      // Bust image cache so new CSP shows immediately
      setLastImageUpdate(Date.now())

      // Refresh metadata
      if (onRefresh) {
        await onRefresh()
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

  // Capture HD CSP - uses active alt's pose if one is selected
  const handleCaptureHdCsp = async () => {
    if (!cspManagerSkin) return

    const scaleNum = parseInt(hdResolution.replace('x', ''))
    setCapturingHdCsp(true)

    try {
      // Check if there's an active alt CSP - if so, regenerate HD for that alt using its pose
      const activeAltId = cspManagerSkin.active_csp_id
      const requestBody = {
        action: 'regenerate-hd',
        scale: scaleNum
      }

      if (activeAltId) {
        // Regenerate HD for the active alt CSP (uses its pose if available)
        requestBody.altId = activeAltId
      } else {
        // Regenerate HD for main CSP (uses default pose)
        requestBody.target = 'main'
      }

      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        }
      )

      const data = await response.json()

      if (data.success) {
        if (!activeAltId) {
          // Update main CSP HD info
          setHdCspInfo({
            exists: true,
            resolution: `${scaleNum}x`,
            size: data.size || 'HD'
          })
        } else if (data.newHdAlt) {
          // New HD alt was created - add to local state
          const newHdAlt = {
            id: data.newHdAlt.id,
            url: data.newHdAlt.url,
            poseName: data.newHdAlt.poseName,
            isHd: true,
            file: null
          }
          setAlternativeCsps(prev => [...prev, newHdAlt])
          // Also update editingItem
          if (onUpdateEditingItemAlts) {
            onUpdateEditingItemAlts(prev => [...prev, newHdAlt])
          }
        }
        // Bust image cache so the new HD CSP shows immediately
        setLastImageUpdate(Date.now())
        // Refresh metadata to get updated data
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

  // Upload main CSP with optional HD version
  const handleUploadMainCsp = async ({ normalFile, hdFile }) => {
    if (!cspManagerSkin) return
    if (!normalFile && !hdFile) return

    try {
      // Upload normal CSP if provided
      if (normalFile) {
        const formData = new FormData()
        formData.append('character', cspManagerSkin.character)
        formData.append('skinId', cspManagerSkin.id)
        formData.append('csp', normalFile)

        const response = await fetch(`${API_URL}/storage/costumes/update-csp`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()
        if (!data.success) {
          alert(`Failed to upload CSP: ${data.error}`)
          return
        }
      }

      // Upload HD CSP if provided
      if (hdFile) {
        const formData = new FormData()
        formData.append('character', cspManagerSkin.character)
        formData.append('skinId', cspManagerSkin.id)
        formData.append('csp', hdFile)
        formData.append('isHd', 'true')

        const response = await fetch(`${API_URL}/storage/costumes/update-csp`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()
        if (!data.success) {
          alert(`Failed to upload HD CSP: ${data.error}`)
          return
        }

        // Update HD info
        setHdCspInfo({
          exists: true,
          resolution: 'Custom',
          size: 'HD'
        })
      }

      // Bust image cache and refresh
      setLastImageUpdate(Date.now())
      if (onRefresh) {
        await onRefresh()
      }
    } catch (err) {
      alert(`Error uploading CSP: ${err.message}`)
    }
  }

  // Upload alternative CSP with optional HD version
  const handleUploadAltCsp = async ({ normalFile, hdFile }) => {
    if (!cspManagerSkin) return
    if (!normalFile && !hdFile) return

    try {
      let newAltId = null

      // Upload normal alt CSP if provided
      if (normalFile) {
        const formData = new FormData()
        formData.append('action', 'add')
        formData.append('file', normalFile)

        const response = await fetch(
          `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
          { method: 'POST', body: formData }
        )

        const data = await response.json()

        if (data.success) {
          newAltId = data.altId
          const newAlt = {
            id: data.altId,
            url: data.url,
            poseName: null,
            isHd: false,
            file: null
          }
          setAlternativeCsps(prev => [...prev, newAlt])
          if (onUpdateEditingItemAlts) {
            onUpdateEditingItemAlts(prev => [...prev, newAlt])
          }
        } else {
          alert(`Failed to add CSP: ${data.error}`)
          return
        }
      }

      // Upload HD alt CSP if provided
      if (hdFile) {
        const formData = new FormData()
        formData.append('action', 'add')
        formData.append('file', hdFile)
        formData.append('isHd', 'true')
        if (newAltId) {
          formData.append('pairWithAltId', newAltId)
        }

        const response = await fetch(
          `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
          { method: 'POST', body: formData }
        )

        const data = await response.json()

        if (data.success) {
          const newHdAlt = {
            id: data.altId,
            url: data.url,
            poseName: null,
            isHd: true,
            file: null
          }
          setAlternativeCsps(prev => [...prev, newHdAlt])
          if (onUpdateEditingItemAlts) {
            onUpdateEditingItemAlts(prev => [...prev, newHdAlt])
          }
        } else {
          alert(`Failed to add HD CSP: ${data.error}`)
        }
      }

      setLastImageUpdate(Date.now())
      if (onRefresh) {
        onRefresh()
      }
    } catch (err) {
      alert(`Error uploading CSP: ${err.message}`)
    }
  }

  // Reset to original CSP (clear active_csp_id)
  const handleResetToOriginal = async () => {
    if (!cspManagerSkin) return

    try {
      const response = await fetch(
        `${API_URL}/storage/costumes/${encodeURIComponent(cspManagerSkin.character)}/${encodeURIComponent(cspManagerSkin.id)}/csp/manage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'reset' })
        }
      )

      const data = await response.json()

      if (data.success) {
        setLastImageUpdate(Date.now())
        if (onRefresh) {
          onRefresh()
        }
        setCspManagerSkin(prev => ({
          ...prev,
          active_csp_id: null
        }))
        // Update editingItem so Edit Modal shows original CSP immediately
        if (onUpdateEditingItemActiveCsp) {
          onUpdateEditingItemActiveCsp(null)
        }
      } else {
        alert(`Failed to reset CSP: ${data.error}`)
      }
    } catch (err) {
      alert(`Error resetting CSP: ${err.message}`)
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
    handleRegenerateAltHd,
    handleResetToOriginal,
    handleUploadMainCsp,
    handleUploadAltCsp
  }
}
