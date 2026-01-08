/**
 * useXdeltaProgress Hook
 *
 * Manages WebSocket connection for real-time XDelta build/create progress updates.
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
  fetchXdeltaPatches
}) {
  const socketRef = useRef(null)

  useEffect(() => {
    const socket = io(BACKEND_URL)
    socketRef.current = socket

    socket.on('connect', () => {
      console.log('Connected to WebSocket for xdelta progress')
    })

    // XDelta build progress events
    socket.on('xdelta_progress', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildProgress(data.percentage)
        setXdeltaBuildMessage(data.message)
      }
    })

    socket.on('xdelta_complete', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildProgress(100)
        setXdeltaBuildFilename(data.filename)
        setXdeltaBuildState('complete')
      }
    })

    socket.on('xdelta_error', (data) => {
      if (xdeltaBuildPatch && data.patch_id === xdeltaBuildPatch.id) {
        setXdeltaBuildError(data.error)
        setXdeltaBuildState('error')
      }
    })

    // XDelta create progress events
    socket.on('xdelta_create_progress', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateProgress(data.percentage)
        setXdeltaCreateMessage(data.message)
      }
    })

    socket.on('xdelta_create_complete', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateProgress(100)
        setXdeltaCreateResult(data)
        setXdeltaCreateState('complete')
        // Refresh patches list
        fetchXdeltaPatches()
      }
    })

    socket.on('xdelta_create_error', (data) => {
      if (xdeltaCreateId && data.create_id === xdeltaCreateId) {
        setXdeltaCreateError(data.error)
        setXdeltaCreateState('error')
      }
    })

    return () => {
      socket.disconnect()
    }
  }, [
    BACKEND_URL,
    xdeltaBuildPatch,
    xdeltaCreateId,
    setXdeltaBuildProgress,
    setXdeltaBuildMessage,
    setXdeltaBuildFilename,
    setXdeltaBuildState,
    setXdeltaBuildError,
    setXdeltaCreateProgress,
    setXdeltaCreateMessage,
    setXdeltaCreateResult,
    setXdeltaCreateState,
    setXdeltaCreateError,
    fetchXdeltaPatches
  ])

  return { socketRef }
}
