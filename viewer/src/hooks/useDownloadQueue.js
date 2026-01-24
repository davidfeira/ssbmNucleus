import { useState, useCallback, useRef } from 'react'

/**
 * Download phases for the state machine
 */
export const DOWNLOAD_PHASES = {
  IDLE: 'idle',
  DOWNLOADING: 'downloading',
  IMPORTING: 'importing',
  COMPLETE: 'complete',
  ERROR: 'error'
}

/**
 * Custom hook for managing a download queue with sequential processing
 * Prevents data corruption from concurrent imports
 *
 * @returns {Object} Download queue state and controls
 */
export function useDownloadQueue() {
  const [currentDownload, setCurrentDownload] = useState(null)
  const [phase, setPhase] = useState(DOWNLOAD_PHASES.IDLE)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // Queue for pending downloads
  const queueRef = useRef([])
  const isProcessingRef = useRef(false)

  /**
   * Process the next download in the queue
   */
  const processNext = useCallback(async () => {
    if (isProcessingRef.current || queueRef.current.length === 0) {
      return
    }

    isProcessingRef.current = true
    const download = queueRef.current.shift()

    setCurrentDownload(download)
    setPhase(DOWNLOAD_PHASES.DOWNLOADING)
    setError(null)
    setResult(null)

    try {
      // Download the file
      const response = await fetch(download.url)
      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`)
      }
      const blob = await response.blob()

      // Switch to importing phase
      setPhase(DOWNLOAD_PHASES.IMPORTING)

      // Create FormData for import
      const formData = new FormData()
      formData.append('file', blob, `${download.name || 'mod'}.zip`)

      if (download.title) {
        formData.append('custom_title', download.title)
      }

      // Call the import API
      const importResponse = await fetch('http://127.0.0.1:5000/api/mex/import/file', {
        method: 'POST',
        body: formData
      })

      const importResult = await importResponse.json()

      // Check for slippi dialog (special case that needs user interaction)
      if (importResult.type === 'slippi_dialog') {
        setResult({
          ...importResult,
          needsSlippiChoice: true,
          blob,
          downloadName: download.name,
          downloadTitle: download.title
        })
        setPhase(DOWNLOAD_PHASES.COMPLETE)
        return
      }

      if (importResult.success) {
        setResult({ success: true, message: `Successfully imported: ${download.title || download.name || 'mod'}` })
        setPhase(DOWNLOAD_PHASES.COMPLETE)
      } else {
        throw new Error(importResult.error || 'Import failed')
      }
    } catch (err) {
      console.error('[DownloadQueue] Error:', err)
      setError(err.message)
      setPhase(DOWNLOAD_PHASES.ERROR)
    }
  }, [])

  /**
   * Queue a download for processing
   * @param {Object} download - Download info with url, name, title
   */
  const queueDownload = useCallback((download) => {
    queueRef.current.push(download)
    processNext()
  }, [processNext])

  /**
   * Clear the current download state (after user dismisses modal)
   */
  const clearDownload = useCallback(() => {
    setCurrentDownload(null)
    setPhase(DOWNLOAD_PHASES.IDLE)
    setError(null)
    setResult(null)
    isProcessingRef.current = false

    // Process next in queue if any
    if (queueRef.current.length > 0) {
      setTimeout(processNext, 100)
    }
  }, [processNext])

  /**
   * Retry import with slippi action (after user makes choice)
   * @param {string} action - 'fix' or 'import_as_is'
   * @returns {Promise<Object>} Import result
   */
  const retryWithSlippiAction = useCallback(async (action) => {
    if (!result?.blob) {
      throw new Error('No pending import data')
    }

    setPhase(DOWNLOAD_PHASES.IMPORTING)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', result.blob, `${result.downloadName || 'mod'}.zip`)
      formData.append('slippi_action', action)

      if (result.downloadTitle) {
        formData.append('custom_title', result.downloadTitle)
      }

      const importResponse = await fetch('http://127.0.0.1:5000/api/mex/import/file', {
        method: 'POST',
        body: formData
      })

      const importResult = await importResponse.json()

      if (importResult.success) {
        setResult({ success: true, message: `Successfully imported: ${result.downloadTitle || result.downloadName || 'mod'}` })
        setPhase(DOWNLOAD_PHASES.COMPLETE)
        return importResult
      } else {
        throw new Error(importResult.error || 'Import failed')
      }
    } catch (err) {
      console.error('[DownloadQueue] Slippi retry error:', err)
      setError(err.message)
      setPhase(DOWNLOAD_PHASES.ERROR)
      throw err
    }
  }, [result])

  return {
    // State
    currentDownload,
    phase,
    error,
    result,
    isDownloading: phase !== DOWNLOAD_PHASES.IDLE,
    queueLength: queueRef.current.length,

    // Actions
    queueDownload,
    clearDownload,
    retryWithSlippiAction
  }
}
