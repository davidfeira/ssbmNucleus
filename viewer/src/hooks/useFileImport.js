/**
 * useFileImport Hook
 *
 * Manages file import functionality including:
 * - File upload and detection
 * - Slippi safety dialog handling
 * - Import success/error messages
 */

import { useState } from 'react'
import { playSound } from '../utils/sounds'

export function useFileImport({
  mode,
  API_URL,
  onRefresh,
  fetchStageVariants
}) {
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [showSlippiDialog, setShowSlippiDialog] = useState(false)
  const [slippiDialogData, setSlippiDialogData] = useState(null)
  const [pendingFile, setPendingFile] = useState(null)

  const handleFileImport = async (event, slippiAction = null) => {
    const file = slippiAction ? pendingFile : event.target.files[0]
    if (!file) return

    setImporting(true)
    setImportMessage('Uploading and detecting mod type...')

    try {
      const formData = new FormData()
      formData.append('file', file)
      if (slippiAction) {
        formData.append('slippi_action', slippiAction)
      }

      const response = await fetch(`${API_URL}/import/file`, {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()

      // Check if we need to show slippi dialog
      if (data.type === 'slippi_dialog') {
        setSlippiDialogData(data)
        setPendingFile(file)
        setShowSlippiDialog(true)
        setImporting(false)
        setImportMessage('')
        if (event && event.target) event.target.value = null
        return
      }

      if (data.success) {
        playSound('newSkin')
        const typeMsg = data.type === 'character'
          ? `${data.imported_count} costume(s)`
          : `${data.stage} stage`
        setImportMessage(`✓ Imported ${typeMsg}! Refreshing...`)

        // Refresh metadata
        await onRefresh()

        // If we imported a stage, also refresh stage variants
        if (data.type === 'stage' && mode === 'stages') {
          await fetchStageVariants()
        }

        setImportMessage(`✓ Successfully imported ${typeMsg}!`)
        setTimeout(() => {
          setImporting(false)
          setImportMessage('')
        }, 2000)
      } else {
        playSound('error')
        setImportMessage(`✗ Import failed: ${data.error}`)
        setTimeout(() => {
          setImporting(false)
          setImportMessage('')
        }, 5000)
      }
    } catch (err) {
      playSound('error')
      setImportMessage(`✗ Error: ${err.message}`)
      setTimeout(() => {
        setImporting(false)
        setImportMessage('')
      }, 5000)
    }

    // Reset file input
    if (event && event.target) event.target.value = null
  }

  const handleSlippiChoice = (choice) => {
    setShowSlippiDialog(false)
    if (choice === 'cancel') {
      setPendingFile(null)
      setSlippiDialogData(null)
      return
    }
    handleFileImport(null, choice)
  }

  return {
    // State
    importing,
    importMessage,
    showSlippiDialog,
    setShowSlippiDialog,
    slippiDialogData,
    setSlippiDialogData,
    pendingFile,
    setPendingFile,

    // Handlers
    handleFileImport,
    handleSlippiChoice
  }
}
