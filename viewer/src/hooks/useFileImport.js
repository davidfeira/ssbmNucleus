/**
 * useFileImport Hook — the one import pipeline for the whole vault.
 *
 * Feeds files (from the floating Import button, drag-and-drop, or any legacy
 * input) to the backend's unified /import/file endpoint, which auto-detects
 * costumes, stages, custom characters, custom stages (incl. classic stage.yml
 * packages), bundles, xdelta patches, and menu mods. Handles:
 * - Slippi safety dialog (single file) / auto-fix (batch)
 * - Duplicate dialog (single file) / auto-skip (batch)
 * - type-aware refresh of whichever vault list the import landed in
 * - import success/error messages (backend messages are user-ready)
 */

import { useState } from 'react'
import { playSound } from '../utils/sounds'

// What each successful import type means for UI refresh + summary counting.
const TYPE_LABELS = {
  character: 'costume(s)',
  stage: 'stage variant(s)',
  custom_character: 'custom character(s)',
  custom_stage: 'custom stage(s)',
  bundle: 'bundle(s)',
  patch: 'patch(es)',
  menu_mod: 'menu mod(s)',
}

export function useFileImport({
  API_URL,
  refreshers = {}
}) {
  const [importing, setImporting] = useState(false)
  const [importMessage, setImportMessage] = useState('')
  const [showSlippiDialog, setShowSlippiDialog] = useState(false)
  const [slippiDialogData, setSlippiDialogData] = useState(null)
  const [pendingFile, setPendingFile] = useState(null)
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false)
  const [duplicateDialogData, setDuplicateDialogData] = useState(null)

  const importSingleFile = async (file, slippiAction = null, duplicateAction = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (slippiAction) formData.append('slippi_action', slippiAction)
    if (duplicateAction) formData.append('duplicate_action', duplicateAction)

    // Let the backend capture an in-game screenshot for stage variants that
    // ship without one (background job; needs the ISO + Dolphin to boot).
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    const slippiDolphinPath = localStorage.getItem('slippi_dolphin_path')
    if (vanillaIsoPath) formData.append('vanillaIsoPath', vanillaIsoPath)
    if (slippiDolphinPath) formData.append('slippiDolphinPath', slippiDolphinPath)

    const response = await fetch(`${API_URL}/import/file`, {
      method: 'POST',
      body: formData,
    })
    return await response.json()
  }

  // Refresh whichever lists the imported types touch (each at most once).
  const refreshForTypes = async (types) => {
    await refreshers.metadata?.()
    if (types.has('stage')) await refreshers.stageVariants?.()
    if (types.has('custom_character')) await refreshers.customCharacters?.()
    if (types.has('custom_stage')) await refreshers.customStages?.()
    if (types.has('patch')) await refreshers.patches?.()
    if (types.has('bundle')) await refreshers.bundles?.()
  }

  const countItems = (data) =>
    data.imported_count
    ?? (data.patches?.length || data.mods?.length)
    ?? 1

  const successMessage = (data) => {
    // The backend's messages are user-ready ("Imported custom stage: X
    // (converted from classic m-ex format)", "— capturing screenshot in the
    // background", ...) so prefer them.
    if (data.message) return `✓ ${data.message}`
    const label = TYPE_LABELS[data.type] || 'item(s)'
    return `✓ Imported ${countItems(data)} ${label}`
  }

  const finishSoon = (delay = 3000) => {
    setTimeout(() => {
      setImporting(false)
      setImportMessage('')
    }, delay)
  }

  // Accepts a DOM change event, a FileList, or an array of Files.
  const normalizeFiles = (eventOrFiles) => {
    if (!eventOrFiles) return []
    if (eventOrFiles.target?.files) return Array.from(eventOrFiles.target.files)
    if (typeof eventOrFiles.length === 'number') return Array.from(eventOrFiles)
    return []
  }

  const handleFileImport = async (eventOrFiles, slippiAction = null) => {
    // Handle slippi action continuation (single file)
    if (slippiAction && pendingFile) {
      setImporting(true)
      setImportMessage('Applying Slippi fix...')
      try {
        const data = await importSingleFile(pendingFile, slippiAction)
        if (data.success) {
          playSound(data.camera_sound ? 'camera' : 'newSkin')
          setImportMessage(successMessage(data))
          await refreshForTypes(new Set([data.type]))
        } else {
          playSound('error')
          setImportMessage(`✗ Import failed: ${data.error}`)
        }
      } catch (err) {
        playSound('error')
        setImportMessage(`✗ Error: ${err.message}`)
      }
      setPendingFile(null)
      finishSoon(2000)
      return
    }

    const files = normalizeFiles(eventOrFiles)
    if (files.length === 0) return

    setImporting(true)
    let successCount = 0
    let errorCount = 0
    let totalItems = 0
    let skippedCount = 0
    let cameraSoundCount = 0
    let lastError = null
    let lastSuccess = null
    const importedTypes = new Set()

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
            if (eventOrFiles?.target) eventOrFiles.target.value = null
            return
          } else {
            // For batch import, auto-fix slippi issues
            const fixData = await importSingleFile(file, 'fix')
            if (fixData.success) {
              successCount++
              totalItems += countItems(fixData)
              importedTypes.add(fixData.type)
              lastSuccess = fixData
              if (fixData.camera_sound) cameraSoundCount++
            } else {
              errorCount++
              lastError = fixData.error
            }
            continue
          }
        }

        // Check for duplicate dialog
        if (data.type === 'duplicate_dialog') {
          if (files.length === 1) {
            setDuplicateDialogData(data)
            setPendingFile(file)
            setShowDuplicateDialog(true)
            setImporting(false)
            setImportMessage('')
            if (eventOrFiles?.target) eventOrFiles.target.value = null
            return
          } else {
            // For batch import, auto-skip duplicates
            skippedCount++
            continue
          }
        }

        if (data.success) {
          successCount++
          totalItems += countItems(data)
          importedTypes.add(data.type)
          lastSuccess = data
          if (data.camera_sound) cameraSoundCount++
        } else {
          errorCount++
          lastError = data.error
        }
      } catch (err) {
        errorCount++
        lastError = err.message
      }
    }

    await refreshForTypes(importedTypes)

    if (successCount > 0) {
      playSound(cameraSoundCount > 0 ? 'camera' : 'newSkin')
    }
    if (errorCount > 0 && successCount === 0) {
      playSound('error')
    }

    // Summary. Single file: the backend message (or specific error) verbatim.
    // Batch: counts by what actually happened.
    let summary
    if (files.length === 1) {
      summary = successCount
        ? successMessage(lastSuccess)
        : skippedCount
          ? 'Skipped (already owned)'
          : `✗ ${lastError || 'Import failed'}`
    } else {
      const typeBreakdown = [...importedTypes]
        .map(t => TYPE_LABELS[t] || t).join(', ')
      const parts = [`✓ Imported ${totalItems} item(s) from ${successCount} file(s)`]
      if (typeBreakdown) parts.push(`(${typeBreakdown})`)
      if (skippedCount) parts.push(`· ${skippedCount} skipped, already owned`)
      if (errorCount) parts.push(`· ${errorCount} failed${lastError ? `: ${lastError}` : ''}`)
      summary = successCount === 0 && errorCount > 0
        ? `✗ ${errorCount} failed${lastError ? `: ${lastError}` : ''}`
        : parts.join(' ')
    }
    setImportMessage(summary)
    finishSoon(errorCount > 0 ? 6000 : 3500)

    // Reset file input
    if (eventOrFiles?.target) eventOrFiles.target.value = null
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

  const handleDuplicateChoice = async (choice) => {
    setShowDuplicateDialog(false)
    const file = pendingFile
    setPendingFile(null)
    setDuplicateDialogData(null)

    if (choice === 'import_anyway') {
      setImporting(true)
      setImportMessage('Importing...')
      try {
        const data = await importSingleFile(file, null, 'import_anyway')
        if (data.success) {
          playSound(data.camera_sound ? 'camera' : 'newSkin')
          setImportMessage(successMessage(data))
          await refreshForTypes(new Set([data.type]))
        } else {
          playSound('error')
          setImportMessage(`✗ Import failed: ${data.error}`)
        }
      } catch (err) {
        playSound('error')
        setImportMessage(`✗ Error: ${err.message}`)
      }
      finishSoon(2000)
    } else {
      // skip
      setImportMessage('Skipped (already owned)')
      setTimeout(() => {
        setImportMessage('')
      }, 2000)
    }
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
    showDuplicateDialog,
    duplicateDialogData,

    // Handlers
    handleFileImport,
    handleSlippiChoice,
    handleDuplicateChoice
  }
}
