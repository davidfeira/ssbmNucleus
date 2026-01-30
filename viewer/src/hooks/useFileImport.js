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

  const importSingleFile = async (file, slippiAction = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (slippiAction) {
      formData.append('slippi_action', slippiAction)
    }

    const response = await fetch(`${API_URL}/import/file`, {
      method: 'POST',
      body: formData,
    })
    return await response.json()
  }

  const handleFileImport = async (event, slippiAction = null) => {
    // Handle slippi action continuation (single file)
    if (slippiAction && pendingFile) {
      setImporting(true)
      setImportMessage('Applying Slippi fix...')
      try {
        const data = await importSingleFile(pendingFile, slippiAction)
        if (data.success) {
          playSound('newSkin')
          const typeMsg = data.type === 'character'
            ? `${data.imported_count} costume(s)`
            : `${data.stage} stage`
          setImportMessage(`✓ Imported ${typeMsg}!`)
          await onRefresh()
          if (data.type === 'stage' && mode === 'stages') {
            await fetchStageVariants()
          }
        } else {
          playSound('error')
          setImportMessage(`✗ Import failed: ${data.error}`)
        }
      } catch (err) {
        playSound('error')
        setImportMessage(`✗ Error: ${err.message}`)
      }
      setPendingFile(null)
      setTimeout(() => {
        setImporting(false)
        setImportMessage('')
      }, 2000)
      return
    }

    const files = Array.from(event.target.files || [])
    if (files.length === 0) return

    setImporting(true)
    let successCount = 0
    let errorCount = 0
    let totalCostumes = 0

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setImportMessage(`Importing ${i + 1}/${files.length}: ${file.name}...`)

      try {
        const data = await importSingleFile(file)

        // Check if we need to show slippi dialog (only for single file)
        if (data.type === 'slippi_dialog') {
          if (files.length === 1) {
            setSlippiDialogData(data)
            setPendingFile(file)
            setShowSlippiDialog(true)
            setImporting(false)
            setImportMessage('')
            if (event && event.target) event.target.value = null
            return
          } else {
            // For batch import, auto-fix slippi issues
            const fixData = await importSingleFile(file, 'fix')
            if (fixData.success) {
              successCount++
              totalCostumes += fixData.imported_count || 1
            } else {
              errorCount++
            }
            continue
          }
        }

        if (data.success) {
          successCount++
          totalCostumes += data.imported_count || 1
          if (data.type === 'stage' && mode === 'stages') {
            await fetchStageVariants()
          }
        } else {
          errorCount++
        }
      } catch (err) {
        errorCount++
      }
    }

    // Final refresh and summary
    await onRefresh()

    if (successCount > 0) {
      playSound('newSkin')
    }
    if (errorCount > 0 && successCount === 0) {
      playSound('error')
    }

    const summary = errorCount > 0
      ? `✓ Imported ${totalCostumes} costume(s) from ${successCount} files (${errorCount} failed)`
      : `✓ Imported ${totalCostumes} costume(s) from ${successCount} files!`
    setImportMessage(summary)

    setTimeout(() => {
      setImporting(false)
      setImportMessage('')
    }, 3000)

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
