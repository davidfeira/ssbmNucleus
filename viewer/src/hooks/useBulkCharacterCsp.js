/**
 * useBulkCharacterCsp
 *
 * Drives the per-character BULK CSP retake flow: pick any number of a character's
 * costumes, re-render each one's portrait with its own active pose through the
 * persistent CSP render pool, review the before/after grid, and apply the ones
 * you keep. The character analog of useBulkStageCapture.
 *
 * Phases: 'select' -> 'retaking' -> 'review'. The backend renders only (writes
 * nothing) and streams csp_retake_item / csp_retake_complete / csp_retake_error
 * over a short-lived socket; apply reuses the single-costume /generate-csp
 * endpoint (one call per kept costume), so nothing is overwritten until Apply.
 */
import { useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../config'
import { playSound } from '../utils/sounds'

export function useBulkCharacterCsp({ character, onApplied } = {}) {
  const [phase, setPhase] = useState('select')        // select | retaking | review
  const [selected, setSelected] = useState(() => new Set())  // skinIds chosen to retake
  const [progress, setProgress] = useState(null)      // { done, total, message }
  const [results, setResults] = useState([])          // [{ skinId, ok, dataUri, poseName, error }]
  const [keep, setKeep] = useState(() => new Set())   // skinIds to apply (review)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState(null)
  const socketRef = useRef(null)
  const resultsRef = useRef([])                       // authoritative list (avoids stale closures)

  const cleanupSocket = () => {
    if (socketRef.current) {
      try { socketRef.current.disconnect() } catch (e) { /* ignore */ }
      socketRef.current = null
    }
  }

  const reset = () => {
    cleanupSocket()
    resultsRef.current = []
    setPhase('select'); setProgress(null); setResults([]); setKeep(new Set())
    setSelected(new Set()); setApplying(false); setError(null)
  }

  const toggle = (skinId) => setSelected((prev) => {
    const next = new Set(prev)
    next.has(skinId) ? next.delete(skinId) : next.add(skinId)
    return next
  })
  const selectAll = (skinIds) => setSelected(new Set(skinIds))
  const clearSelection = () => setSelected(new Set())

  const startRetake = async (skinIds) => {
    if (!skinIds.length) return
    playSound('start')
    resultsRef.current = []
    setPhase('retaking'); setError(null); setResults([])
    setProgress({ done: 0, total: skinIds.length, message: `Retaking 0/${skinIds.length}…` })

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('csp_retake_item', (item) => {
      resultsRef.current = [...resultsRef.current, item]
      setResults(resultsRef.current)
      setProgress({ done: item.done, total: item.total,
        message: `Retaking ${item.done}/${item.total}…` })
    })
    socket.on('csp_retake_complete', () => {
      // default: keep every costume that rendered (the user can deselect)
      setKeep(new Set(resultsRef.current.filter((r) => r.ok).map((r) => r.skinId)))
      setPhase('review')
      playSound(resultsRef.current.some((r) => r.ok) ? 'achievement' : 'error')
      cleanupSocket()
    })
    socket.on('csp_retake_error', (d) => {
      setError(d.error || 'Bulk retake failed')
      setPhase('select'); playSound('error'); cleanupSocket()
    })

    try {
      const res = await fetch(`${API_URL}/storage/costumes/batch-retake-csp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character, skinIds }),
      })
      const data = await res.json()
      if (!data.success) {
        setError(data.error || 'Failed to start bulk retake')
        setPhase('select'); playSound('error'); cleanupSocket()
      }
    } catch (err) {
      setError(`Failed to start bulk retake: ${err.message}`)
      setPhase('select'); playSound('error'); cleanupSocket()
    }
  }

  const toggleKeep = (skinId) => setKeep((prev) => {
    const next = new Set(prev)
    next.has(skinId) ? next.delete(skinId) : next.add(skinId)
    return next
  })

  const applyKept = async () => {
    const toApply = results.filter((r) => r.ok && r.dataUri && keep.has(r.skinId))
    if (!toApply.length) return 0
    setApplying(true); setError(null)
    let applied = 0
    for (const r of toApply) {
      try {
        // Reuse the single-costume retake's apply: derives SD + HD from the HD
        // preview and writes it to the costume's active portrait.
        const res = await fetch(`${API_URL}/storage/costumes/generate-csp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ character, skinId: r.skinId, apply: true, imageData: r.dataUri }),
        })
        const data = await res.json()
        if (data.success) applied++
      } catch (e) { /* keep going; the count reflects it */ }
    }
    setApplying(false)
    playSound(applied ? 'achievement' : 'error')
    // Never let a refresh callback error bubble up and abort the modal close.
    try { if (onApplied) onApplied(applied) } catch (e) { /* ignore */ }
    return applied
  }

  return {
    phase, selected, toggle, selectAll, clearSelection,
    progress, results, keep, toggleKeep, applying, error,
    startRetake, applyKept, reset, setError,
  }
}
