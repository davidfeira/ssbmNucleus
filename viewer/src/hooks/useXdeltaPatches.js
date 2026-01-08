/**
 * useXdeltaPatches Hook
 *
 * Manages XDelta patches including:
 * - Fetching, importing, editing, deleting patches
 * - Building ISOs from patches
 * - Creating new patches from modded ISOs
 * - Download functionality
 */

import { useState } from 'react'

export function useXdeltaPatches({ API_URL }) {
  // Patches list state
  const [xdeltaPatches, setXdeltaPatches] = useState([])

  // Import modal state
  const [showXdeltaImportModal, setShowXdeltaImportModal] = useState(false)
  const [xdeltaImportData, setXdeltaImportData] = useState({ name: '', description: '', file: null, image: null })
  const [importingXdelta, setImportingXdelta] = useState(false)

  // Edit modal state
  const [showXdeltaEditModal, setShowXdeltaEditModal] = useState(false)
  const [editingXdelta, setEditingXdelta] = useState(null)

  // Build ISO modal state
  const [showXdeltaBuildModal, setShowXdeltaBuildModal] = useState(false)
  const [xdeltaBuildState, setXdeltaBuildState] = useState('idle') // 'idle', 'building', 'complete', 'error'
  const [xdeltaBuildPatch, setXdeltaBuildPatch] = useState(null)
  const [xdeltaBuildFilename, setXdeltaBuildFilename] = useState(null)
  const [xdeltaBuildError, setXdeltaBuildError] = useState(null)
  const [xdeltaBuildProgress, setXdeltaBuildProgress] = useState(0)
  const [xdeltaBuildMessage, setXdeltaBuildMessage] = useState('')

  // Create patch modal state
  const [showXdeltaCreateModal, setShowXdeltaCreateModal] = useState(false)
  const [xdeltaCreateData, setXdeltaCreateData] = useState({ name: '', description: '', moddedIsoPath: '' })
  const [xdeltaCreateState, setXdeltaCreateState] = useState('idle') // 'idle', 'creating', 'complete', 'error'
  const [xdeltaCreateId, setXdeltaCreateId] = useState(null)
  const [xdeltaCreateProgress, setXdeltaCreateProgress] = useState(0)
  const [xdeltaCreateMessage, setXdeltaCreateMessage] = useState('')
  const [xdeltaCreateError, setXdeltaCreateError] = useState(null)
  const [xdeltaCreateResult, setXdeltaCreateResult] = useState(null)

  // Fetch patches list
  const fetchXdeltaPatches = async () => {
    try {
      const response = await fetch(`${API_URL}/xdelta/list`)
      if (!response.ok) {
        console.error('Failed to fetch xdelta patches: Server returned', response.status)
        return
      }
      const text = await response.text()
      if (!text || text.startsWith('<!')) {
        console.error('Failed to fetch xdelta patches: Server returned HTML instead of JSON')
        return
      }
      const data = JSON.parse(text)
      if (data.success) {
        setXdeltaPatches(data.patches)
      }
    } catch (err) {
      console.error('Failed to fetch xdelta patches:', err)
    }
  }

  // Import patch
  const handleImportXdelta = async () => {
    if (!xdeltaImportData.file) {
      alert('Please select an xdelta file')
      return
    }

    setImportingXdelta(true)

    try {
      const formData = new FormData()
      formData.append('file', xdeltaImportData.file)
      formData.append('name', xdeltaImportData.name || xdeltaImportData.file.name.replace('.xdelta', ''))
      formData.append('description', xdeltaImportData.description)
      if (xdeltaImportData.image) {
        formData.append('image', xdeltaImportData.image)
      }

      const response = await fetch(`${API_URL}/xdelta/import`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setShowXdeltaImportModal(false)
        setXdeltaImportData({ name: '', description: '', file: null, image: null })
        await fetchXdeltaPatches()
      } else {
        alert(`Import failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Import error: ${err.message}`)
    } finally {
      setImportingXdelta(false)
    }
  }

  // Build ISO from patch
  const handleBuildXdeltaIso = async (patch) => {
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')

    if (!vanillaIsoPath) {
      alert('No vanilla ISO path set. Please set it in Settings first.')
      return
    }

    // Open modal and set building state
    setXdeltaBuildPatch(patch)
    setXdeltaBuildState('building')
    setXdeltaBuildFilename(null)
    setXdeltaBuildError(null)
    setXdeltaBuildProgress(0)
    setXdeltaBuildMessage('Starting...')
    setShowXdeltaBuildModal(true)

    try {
      const response = await fetch(`${API_URL}/xdelta/build/${patch.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vanillaIsoPath })
      })

      const data = await response.json()

      if (!data.success) {
        setXdeltaBuildError(data.error)
        setXdeltaBuildState('error')
      }
      // If success, we wait for WebSocket events for progress/complete
    } catch (err) {
      setXdeltaBuildError(err.message)
      setXdeltaBuildState('error')
    }
  }

  // Download built ISO
  const handleDownloadXdeltaIso = () => {
    if (!xdeltaBuildFilename) return

    const link = document.createElement('a')
    link.href = `${API_URL}/xdelta/download/${xdeltaBuildFilename}`
    link.download = xdeltaBuildFilename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Close build modal
  const closeXdeltaBuildModal = () => {
    setShowXdeltaBuildModal(false)
    setXdeltaBuildState('idle')
    setXdeltaBuildPatch(null)
    setXdeltaBuildFilename(null)
    setXdeltaBuildError(null)
    setXdeltaBuildProgress(0)
    setXdeltaBuildMessage('')
  }

  // Select modded ISO for creating patch
  const handleSelectModdedIso = async () => {
    try {
      // Use Electron's file dialog if available
      if (window.electron?.openIsoDialog) {
        const result = await window.electron.openIsoDialog()
        if (result) {
          setXdeltaCreateData({ ...xdeltaCreateData, moddedIsoPath: result })
        }
      } else {
        alert('File selection requires the desktop app')
      }
    } catch (err) {
      console.error('Failed to select ISO:', err)
    }
  }

  // Start creating patch
  const handleStartCreateXdelta = async () => {
    if (!xdeltaCreateData.moddedIsoPath) {
      alert('Please select a modded ISO file')
      return
    }

    if (!xdeltaCreateData.name.trim()) {
      alert('Please enter a name for the patch')
      return
    }

    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    if (!vanillaIsoPath) {
      alert('No vanilla ISO path set. Please set it in Settings first.')
      return
    }

    // Switch to creating state
    setXdeltaCreateState('creating')
    setXdeltaCreateProgress(0)
    setXdeltaCreateMessage('Starting...')
    setXdeltaCreateError(null)
    setXdeltaCreateResult(null)

    try {
      const response = await fetch(`${API_URL}/xdelta/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vanillaIsoPath,
          moddedIsoPath: xdeltaCreateData.moddedIsoPath,
          name: xdeltaCreateData.name,
          description: xdeltaCreateData.description
        })
      })

      const data = await response.json()

      if (data.success) {
        setXdeltaCreateId(data.create_id)
      } else {
        setXdeltaCreateError(data.error)
        setXdeltaCreateState('error')
      }
    } catch (err) {
      setXdeltaCreateError(err.message)
      setXdeltaCreateState('error')
    }
  }

  // Close create modal
  const closeXdeltaCreateModal = () => {
    setShowXdeltaCreateModal(false)
    setXdeltaCreateState('idle')
    setXdeltaCreateData({ name: '', description: '', moddedIsoPath: '' })
    setXdeltaCreateId(null)
    setXdeltaCreateProgress(0)
    setXdeltaCreateMessage('')
    setXdeltaCreateError(null)
    setXdeltaCreateResult(null)
  }

  // Download patch file
  const handleDownloadPatch = (patchId) => {
    const link = document.createElement('a')
    link.href = `${API_URL}/xdelta/download-patch/${patchId}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Delete patch
  const handleDeleteXdelta = async (patchId) => {
    if (!confirm('Are you sure you want to delete this patch?')) return

    try {
      const response = await fetch(`${API_URL}/xdelta/delete/${patchId}`, {
        method: 'POST'
      })

      const data = await response.json()

      if (data.success) {
        await fetchXdeltaPatches()
      } else {
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    }
  }

  // Edit patch metadata
  const handleEditXdelta = (patch) => {
    setEditingXdelta({ ...patch })
    setShowXdeltaEditModal(true)
  }

  // Save patch metadata edit
  const handleSaveXdeltaEdit = async () => {
    if (!editingXdelta) return

    try {
      const response = await fetch(`${API_URL}/xdelta/update/${editingXdelta.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editingXdelta.name,
          description: editingXdelta.description
        })
      })

      const data = await response.json()

      if (data.success) {
        setShowXdeltaEditModal(false)
        setEditingXdelta(null)
        await fetchXdeltaPatches()
      } else {
        alert(`Save failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Save error: ${err.message}`)
    }
  }

  // Update patch image
  const handleUpdateXdeltaImage = async (e) => {
    if (!editingXdelta) return

    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('image', file)

    try {
      const response = await fetch(`${API_URL}/xdelta/update-image/${editingXdelta.id}`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setEditingXdelta({ ...editingXdelta, imageUrl: data.imageUrl })
        await fetchXdeltaPatches()
      } else {
        alert(`Image update failed: ${data.error}`)
      }
    } catch (err) {
      alert(`Image update error: ${err.message}`)
    }
  }

  return {
    // State
    xdeltaPatches,
    showXdeltaImportModal,
    setShowXdeltaImportModal,
    xdeltaImportData,
    setXdeltaImportData,
    importingXdelta,
    showXdeltaEditModal,
    setShowXdeltaEditModal,
    editingXdelta,
    setEditingXdelta,
    showXdeltaBuildModal,
    xdeltaBuildState,
    setXdeltaBuildState,
    xdeltaBuildPatch,
    setXdeltaBuildPatch,
    xdeltaBuildFilename,
    setXdeltaBuildFilename,
    xdeltaBuildError,
    setXdeltaBuildError,
    xdeltaBuildProgress,
    setXdeltaBuildProgress,
    xdeltaBuildMessage,
    setXdeltaBuildMessage,
    showXdeltaCreateModal,
    setShowXdeltaCreateModal,
    xdeltaCreateData,
    setXdeltaCreateData,
    xdeltaCreateState,
    setXdeltaCreateState,
    xdeltaCreateId,
    setXdeltaCreateId,
    xdeltaCreateProgress,
    setXdeltaCreateProgress,
    xdeltaCreateMessage,
    setXdeltaCreateMessage,
    xdeltaCreateError,
    setXdeltaCreateError,
    xdeltaCreateResult,
    setXdeltaCreateResult,

    // Handlers
    fetchXdeltaPatches,
    handleImportXdelta,
    handleBuildXdeltaIso,
    handleDownloadXdeltaIso,
    closeXdeltaBuildModal,
    handleSelectModdedIso,
    handleStartCreateXdelta,
    closeXdeltaCreateModal,
    handleDownloadPatch,
    handleDeleteXdelta,
    handleEditXdelta,
    handleSaveXdeltaEdit,
    handleUpdateXdeltaImage
  }
}
