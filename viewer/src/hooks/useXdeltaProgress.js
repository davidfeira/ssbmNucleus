/**
 * useXdeltaProgress Hook
 *
 * Manages WebSocket connection for real-time XDelta build/create progress updates.
 * Also handles bundle import progress events.
 * Listens for progress, complete, and error events from the backend.
 */

import { useEffect, useRef } from 'react'
import { io } from 'socket.io-client'

export function useXdeltaProgress({
  BACKEND_URL,
  xdeltaBuildPatch,
  setXdeltaBuildProgress,
  setXdeltaBuildMessage,
  setXdeltaBuildFilename,
  setXdeltaBuildState,
  setXdeltaBuildError,
  xdeltaCreateId,
  setXdeltaCreateProgress,
  setXdeltaCreateMessage,
  setXdeltaCreateResult,
  setXdeltaCreateState,
  setXdeltaCreateError,
  fetchXdeltaPatches,
  // Bundle import props
  bundleImportId,
  setBundleProgress,
  setBundleMessage,
  setBundleComplete,
  setBundleResult,
  setBundleImporting,
  setBundleError,
  fetchBundles
}) {
  const socketRef = useRef(null)

  // Keep latest values in refs so the socket handlers always see current state
  // without needing to reconnect
  const callbacksRef = useRef({})
  callbacksRef.current = {
    xdeltaBuildPatch,
    setXdeltaBuildProgress,
    setXdeltaBuildMessage,
    setXdeltaBuildFilename,
    setXdeltaBuildState,
    setXdeltaBuildError,
    xdeltaCreateId,
    setXdeltaCreateProgress,
    setXdeltaCreateMessage,
    setXdeltaCreateResult,
    setXdeltaCreateState,
    setXdeltaCreateError,
    fetchXdeltaPatches,
    bundleImportId,
    setBundleProgress,
    setBundleMessage,
    setBundleComplete,
    setBundleResult,
    setBundleImporting,
    setBundleError,
    fetchBundles
  }

  useEffect(() => {
    const socket = io(BACKEND_URL)
    socketRef.current = socket

    socket.on('connect', () => {
      console.log('Connected to WebSocket for xdelta progress')
    })

    // XDelta build progress events
    socket.on('xdelta_progress', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaBuildPatch && data.patch_id === c.xdeltaBuildPatch.id) {
        c.setXdeltaBuildProgress(data.percentage)
        c.setXdeltaBuildMessage(data.message)
      }
    })

    socket.on('xdelta_complete', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaBuildPatch && data.patch_id === c.xdeltaBuildPatch.id) {
        c.setXdeltaBuildProgress(100)
        c.setXdeltaBuildFilename(data.filename)
        c.setXdeltaBuildState('complete')
      }
    })

    socket.on('xdelta_error', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaBuildPatch && data.patch_id === c.xdeltaBuildPatch.id) {
        c.setXdeltaBuildError(data.error)
        c.setXdeltaBuildState('error')
      }
    })

    // XDelta create progress events
    socket.on('xdelta_create_progress', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaCreateId && data.create_id === c.xdeltaCreateId) {
        c.setXdeltaCreateProgress(data.percentage)
        c.setXdeltaCreateMessage(data.message)
      }
    })

    socket.on('xdelta_create_complete', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaCreateId && data.create_id === c.xdeltaCreateId) {
        c.setXdeltaCreateProgress(100)
        c.setXdeltaCreateResult(data)
        c.setXdeltaCreateState('complete')
        c.fetchXdeltaPatches()
      }
    })

    socket.on('xdelta_create_error', (data) => {
      const c = callbacksRef.current
      if (c.xdeltaCreateId && data.create_id === c.xdeltaCreateId) {
        c.setXdeltaCreateError(data.error)
        c.setXdeltaCreateState('error')
      }
    })

    // Bundle import progress events
    socket.on('bundle_import_progress', (data) => {
      const c = callbacksRef.current
      if (c.bundleImportId && data.import_id === c.bundleImportId) {
        c.setBundleProgress?.(data.percentage)
        c.setBundleMessage?.(data.message)
      }
    })

    socket.on('bundle_import_complete', (data) => {
      const c = callbacksRef.current
      if (c.bundleImportId && data.import_id === c.bundleImportId) {
        c.setBundleProgress?.(100)
        c.setBundleComplete?.(true)
        c.setBundleResult?.(data)
        c.setBundleImporting?.(false)
        c.fetchBundles?.()
      }
    })

    socket.on('bundle_import_error', (data) => {
      const c = callbacksRef.current
      if (c.bundleImportId && data.import_id === c.bundleImportId) {
        c.setBundleError?.(data.error)
        c.setBundleImporting?.(false)
      }
    })

    return () => {
      socket.disconnect()
    }
  }, [BACKEND_URL])

  return { socketRef }
}
