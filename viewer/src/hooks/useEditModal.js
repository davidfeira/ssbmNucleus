/**
 * useEditModal Hook
 *
 * Manages edit modal functionality for costumes and stage variants including:
 * - Edit modal state and visibility
 * - File upload handling (CSP, stock icons, screenshots)
 * - Save/delete/export operations
 * - Preview generation for uploaded files
 * - Slippi safety status management
 */

import { useState } from 'react'
import { playSound } from '../utils/sounds'

export function useEditModal({ API_URL, onRefresh, fetchStageVariants, setLastImageUpdate }) {
  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState(null) // { type: 'costume'/'stage', data: {...} }
  const [editName, setEditName] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [generatingStock, setGeneratingStock] = useState(false)
  const [pendingGeneratedStock, setPendingGeneratedStock] = useState(null) // { dataUri, method }
  const [generatingCsp, setGeneratingCsp] = useState(false)
  const [pendingGeneratedCsp, setPendingGeneratedCsp] = useState(null) // { dataUri, poseName }

  // Confirm dialog state
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [confirmDialogData, setConfirmDialogData] = useState(null)

  // File upload state
  const [newScreenshot, setNewScreenshot] = useState(null) // File object for new screenshot
  const [screenshotPreview, setScreenshotPreview] = useState(null) // Preview URL for new screenshot
  const [newCsp, setNewCsp] = useState(null) // File object for new CSP
  const [cspPreview, setCspPreview] = useState(null) // Preview URL for new CSP
  const [newStock, setNewStock] = useState(null) // File object for new stock
  const [stockPreview, setStockPreview] = useState(null) // Preview URL for new stock

  // Slippi state
  const [editSlippiSafe, setEditSlippiSafe] = useState(null) // Track slippi changes for stages
  const [slippiAdvancedOpen, setSlippiAdvancedOpen] = useState(false) // Collapsible Slippi controls

  // 3D viewer state
  const [show3DViewer, setShow3DViewer] = useState(false)

  // Open edit modal
  const handleEditClick = (type, data) => {
    const item = { type, data }
    const name = type === 'costume' ? data.color : data.name
    setEditingItem(item)
    setEditName(name)
    setSaving(false)
    setDeleting(false)
    setNewScreenshot(null)
    setScreenshotPreview(null)
    setNewCsp(null)
    setCspPreview(null)
    setNewStock(null)
    setStockPreview(null)
    setPendingGeneratedStock(null)
    setPendingGeneratedCsp(null)
    setEditSlippiSafe(type === 'stage' ? data.slippi_safe : null)
    setShowEditModal(true)
  }

  // Handle file changes
  const handleScreenshotChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewScreenshot(file)

    const reader = new FileReader()
    reader.onload = (e) => {
      setScreenshotPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  const handleCspChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewCsp(file)

    const reader = new FileReader()
    reader.onload = (e) => {
      setCspPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  const handleStockChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setNewStock(file)

    const reader = new FileReader()
    reader.onload = (e) => {
      setStockPreview(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  // Save changes
  const handleSave = async () => {
    if (!editName.trim()) {
      playSound('error')
      alert('Name cannot be empty')
      return
    }

    setSaving(true)
    let shouldPlayCameraSound = false

    try {
      // Save name change
      const endpoint = editingItem.type === 'costume'
        ? `${API_URL}/storage/costumes/rename`
        : `${API_URL}/storage/stages/rename`

      const body = editingItem.type === 'costume'
        ? {
            character: editingItem.data.character,
            skinId: editingItem.data.id,
            newName: editName
          }
        : {
            stageFolder: editingItem.data.stageFolder,
            variantId: editingItem.data.id,
            newName: editName
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (!data.success) {
        playSound('error')
        alert(`Save failed: ${data.error}`)
        setSaving(false)
        return
      }

      // If this is a stage and there's a new screenshot, upload it
      if (editingItem.type === 'stage' && newScreenshot) {
        const formData = new FormData()
        formData.append('stageFolder', editingItem.data.stageFolder)
        formData.append('variantId', editingItem.data.id)
        formData.append('screenshot', newScreenshot)

        const screenshotResponse = await fetch(`${API_URL}/storage/stages/update-screenshot`, {
          method: 'POST',
          body: formData
        })

        const screenshotData = await screenshotResponse.json()

        if (!screenshotData.success) {
          playSound('error')
          alert(`Screenshot upload failed: ${screenshotData.error}`)
          setSaving(false)
          return
        }

        shouldPlayCameraSound = true
      }

      // If this is a stage and slippi status changed, save it
      if (editingItem.type === 'stage' && editSlippiSafe !== editingItem.data.slippi_safe) {
        const slippiResponse = await fetch(`${API_URL}/storage/stages/set-slippi`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stageName: editingItem.data.stageFolder,
            variantId: editingItem.data.id,
            slippiSafe: editSlippiSafe
          })
        })

        const slippiData = await slippiResponse.json()

        if (!slippiData.success) {
          playSound('error')
          alert(`Slippi status update failed: ${slippiData.error}`)
          setSaving(false)
          return
        }
      }

      // If this is a character costume and there's a new CSP, upload it
      if (editingItem.type === 'costume' && newCsp) {
        const formData = new FormData()
        formData.append('character', editingItem.data.character)
        formData.append('skinId', editingItem.data.id)
        formData.append('csp', newCsp)

        const cspResponse = await fetch(`${API_URL}/storage/costumes/update-csp`, {
          method: 'POST',
          body: formData
        })

        const cspData = await cspResponse.json()

        if (!cspData.success) {
          playSound('error')
          alert(`CSP upload failed: ${cspData.error}`)
          setSaving(false)
          return
        }

        shouldPlayCameraSound = true
      }

      // If this is a character costume and there's a new stock icon, upload it
      if (editingItem.type === 'costume' && newStock) {
        const formData = new FormData()
        formData.append('character', editingItem.data.character)
        formData.append('skinId', editingItem.data.id)
        formData.append('stock', newStock)

        const stockResponse = await fetch(`${API_URL}/storage/costumes/update-stock`, {
          method: 'POST',
          body: formData
        })

        const stockData = await stockResponse.json()

        if (!stockData.success) {
          playSound('error')
          alert(`Stock icon upload failed: ${stockData.error}`)
          setSaving(false)
          return
        }
      }

      // Refetch data before closing modal
      if (editingItem.type === 'stage') {
        await fetchStageVariants()
      }

      // Always await metadata refresh for costumes (CSP/stock updates)
      await onRefresh()

      // If we uploaded a CSP, stock, or screenshot, bump the cache-busting
      // timestamp so the grid/preview reload the new image (same URL otherwise).
      if (newCsp || newStock || newScreenshot) {
        setLastImageUpdate(Date.now())
      }

      if (shouldPlayCameraSound) {
        playSound('camera')
      }

      setShowEditModal(false)
      setEditingItem(null)
    } catch (err) {
      playSound('error')
      alert(`Save error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  // Replace a stage variant's screenshot with a freshly CAPTURED image (data URI
  // from the in-game capture). Saves immediately via the same endpoint + refresh
  // the manual upload uses, then closes the modal.
  const replaceStageScreenshotWithCapture = async (dataUri) => {
    if (!editingItem || editingItem.type !== 'stage' || !dataUri) return
    setSaving(true)
    try {
      const blob = await (await fetch(dataUri)).blob()
      const formData = new FormData()
      formData.append('stageFolder', editingItem.data.stageFolder)
      formData.append('variantId', editingItem.data.id)
      formData.append('screenshot', blob, `${editingItem.data.id}_screenshot.png`)

      const resp = await fetch(`${API_URL}/storage/stages/update-screenshot`, {
        method: 'POST',
        body: formData
      })
      const data = await resp.json()
      if (!data.success) {
        playSound('error')
        alert(`Screenshot save failed: ${data.error}`)
        return
      }

      await fetchStageVariants()
      await onRefresh()
      setLastImageUpdate(Date.now())
      playSound('camera')
      setShowEditModal(false)
      setEditingItem(null)
    } catch (err) {
      playSound('error')
      alert(`Screenshot save error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  // Derive a stock icon from the costume's DAT colors (vs vanilla) on the
  // backend. Nothing is written yet: the preview is held in
  // pendingGeneratedStock until the user confirms or discards it.
  const handleGenerateStock = async () => {
    if (!editingItem || editingItem.type !== 'costume') return
    setGeneratingStock(true)
    try {
      const response = await fetch(`${API_URL}/storage/costumes/generate-stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id
        })
      })
      const data = await response.json()
      if (!data.success) {
        playSound('error')
        alert(`Stock generation failed: ${data.error}`)
        return
      }

      // Clear any pending manual upload; the compare bar takes over
      setNewStock(null)
      setStockPreview(null)
      setPendingGeneratedStock({ dataUri: data.dataUri, method: data.method })
      playSound('boop')
    } catch (err) {
      playSound('error')
      alert(`Stock generation error: ${err.message}`)
    } finally {
      setGeneratingStock(false)
    }
  }

  // Write the previewed icon for real
  const confirmGeneratedStock = async () => {
    if (!editingItem || !pendingGeneratedStock) return
    setGeneratingStock(true)
    try {
      const response = await fetch(`${API_URL}/storage/costumes/generate-stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id,
          apply: true,
          imageData: pendingGeneratedStock.dataUri
        })
      })
      const data = await response.json()
      if (!data.success) {
        playSound('error')
        alert(`Stock save failed: ${data.error}`)
        return
      }
      setPendingGeneratedStock(null)
      setEditingItem(prev => prev ? {
        ...prev,
        data: { ...prev.data, has_stock: true, stockUrl: data.stockUrl, stock_source: 'generated' }
      } : prev)
      await onRefresh()
      setLastImageUpdate(Date.now())
      playSound('camera')
    } catch (err) {
      playSound('error')
      alert(`Stock save error: ${err.message}`)
    } finally {
      setGeneratingStock(false)
    }
  }

  const discardGeneratedStock = () => {
    setPendingGeneratedStock(null)
    playSound('back')
  }

  // Re-render ("retake") the costume's character-select portrait with the
  // headless renderer, using whichever pose is currently active (the default
  // pose unless a custom-pose alternate is active). Nothing is written yet --
  // the fresh render is held in pendingGeneratedCsp until confirm/discard.
  const handleRetakeCsp = async () => {
    if (!editingItem || editingItem.type !== 'costume') return
    setGeneratingCsp(true)
    try {
      const response = await fetch(`${API_URL}/storage/costumes/generate-csp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id
        })
      })
      const data = await response.json()
      if (!data.success) {
        playSound('error')
        alert(`Portrait render failed: ${data.error}`)
        return
      }

      // Clear any pending manual CSP upload; the retake preview takes over
      setNewCsp(null)
      setCspPreview(null)
      setPendingGeneratedCsp({ dataUri: data.dataUri, poseName: data.poseName })
      playSound('boop')
    } catch (err) {
      playSound('error')
      alert(`Portrait render error: ${err.message}`)
    } finally {
      setGeneratingCsp(false)
    }
  }

  // Write the previewed portrait for real (replaces the active portrait -- the
  // original CSP, or the active pose alternate -- on the backend).
  const confirmGeneratedCsp = async () => {
    if (!editingItem || !pendingGeneratedCsp) return
    setGeneratingCsp(true)
    try {
      const response = await fetch(`${API_URL}/storage/costumes/generate-csp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: editingItem.data.character,
          skinId: editingItem.data.id,
          apply: true,
          imageData: pendingGeneratedCsp.dataUri
        })
      })
      const data = await response.json()
      if (!data.success) {
        playSound('error')
        alert(`Portrait save failed: ${data.error}`)
        return
      }
      setPendingGeneratedCsp(null)
      setEditingItem(prev => prev ? {
        ...prev,
        data: { ...prev.data, has_csp: true }
      } : prev)
      await onRefresh()
      setLastImageUpdate(Date.now())
      playSound('camera')
    } catch (err) {
      playSound('error')
      alert(`Portrait save error: ${err.message}`)
    } finally {
      setGeneratingCsp(false)
    }
  }

  const discardGeneratedCsp = () => {
    setPendingGeneratedCsp(null)
    playSound('back')
  }

  // Delete item - shows confirmation dialog
  const handleDelete = () => {
    const itemName = editingItem.type === 'costume'
      ? `${editingItem.data.character} - ${editingItem.data.color}`
      : editingItem.data.name

    setConfirmDialogData({
      title: 'Delete Item',
      message: `Are you sure you want to delete "${itemName}"? This cannot be undone.`,
      confirmText: 'Delete',
      itemToDelete: editingItem
    })
    setShowConfirmDialog(true)
  }

  // Actually perform the delete after confirmation
  const confirmDelete = async () => {
    const itemToDelete = confirmDialogData?.itemToDelete || editingItem
    setShowConfirmDialog(false)
    setConfirmDialogData(null)
    setDeleting(true)

    try {
      const endpoint = itemToDelete.type === 'costume'
        ? `${API_URL}/storage/costumes/delete`
        : `${API_URL}/storage/stages/delete`

      const body = itemToDelete.type === 'costume'
        ? {
            character: itemToDelete.data.character,
            skinId: itemToDelete.data.id
          }
        : {
            stageFolder: itemToDelete.data.stageFolder,
            variantId: itemToDelete.data.id
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Refetch data before closing modal
        if (itemToDelete.type === 'stage') {
          await fetchStageVariants()
        }

        // Always await metadata refresh for costumes
        await onRefresh()

        // Update cache-busting timestamp to force image reload after deletion
        if (itemToDelete.type === 'costume') {
          setLastImageUpdate(Date.now())
        }

        setShowEditModal(false)
        setEditingItem(null)
      } else {
        playSound('error')
        alert(`Delete failed: ${data.error}`)
      }
    } catch (err) {
      playSound('error')
      alert(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
    }
  }

  // Cancel delete confirmation
  const cancelDelete = () => {
    setShowConfirmDialog(false)
    setConfirmDialogData(null)
  }

  // Export item
  const handleExport = async () => {
    setExporting(true)

    try {
      const endpoint = editingItem.type === 'costume'
        ? `${API_URL}/storage/costumes/export`
        : `${API_URL}/storage/stages/export`

      const body = editingItem.type === 'costume'
        ? {
            character: editingItem.data.character,
            skinId: editingItem.data.id,
            colorName: editingItem.data.color
          }
        : {
            stageCode: editingItem.data.stageCode,
            stageName: editingItem.data.stageName,
            variantId: editingItem.data.id,
            variantName: editingItem.data.name
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Trigger download
        const downloadUrl = `${API_URL}/export/mod/${data.filename}`
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = data.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        playSound('error')
        alert(`Export failed: ${data.error}`)
      }
    } catch (err) {
      playSound('error')
      alert(`Export error: ${err.message}`)
    } finally {
      setExporting(false)
    }
  }

  // Cancel and close modal
  const handleCancel = () => {
    playSound('back')
    setShowEditModal(false)
    setEditingItem(null)
    setEditName('')
    setNewScreenshot(null)
    setScreenshotPreview(null)
    setNewCsp(null)
    setCspPreview(null)
    setNewStock(null)
    setStockPreview(null)
    setPendingGeneratedStock(null)
    setPendingGeneratedCsp(null)
    setEditSlippiSafe(null)
  }

  return {
    // State
    showEditModal,
    setShowEditModal,
    editingItem,
    setEditingItem,
    editName,
    setEditName,
    saving,
    deleting,
    exporting,
    generatingStock,
    pendingGeneratedStock,
    generatingCsp,
    pendingGeneratedCsp,
    newScreenshot,
    screenshotPreview,
    newCsp,
    cspPreview,
    newStock,
    stockPreview,
    editSlippiSafe,
    setEditSlippiSafe,
    slippiAdvancedOpen,
    setSlippiAdvancedOpen,
    show3DViewer,
    setShow3DViewer,

    // Confirm dialog state
    showConfirmDialog,
    confirmDialogData,

    // Handlers
    handleEditClick,
    handleScreenshotChange,
    replaceStageScreenshotWithCapture,
    handleCspChange,
    handleStockChange,
    handleGenerateStock,
    confirmGeneratedStock,
    discardGeneratedStock,
    handleRetakeCsp,
    confirmGeneratedCsp,
    discardGeneratedCsp,
    handleSave,
    handleDelete,
    handleExport,
    handleCancel,

    // Confirm dialog handlers
    confirmDelete,
    cancelDelete
  }
}
