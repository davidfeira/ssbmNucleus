/**
 * useBulkStageCapture
 *
 * Drives the BULK DAS stage-screenshot flow: pick any number of variants from the
 * whole vault, capture them all in the throwaway Dolphin (the backend groups them
 * by base stage and packs up to 4 per ISO, behind X/Y/Z/L holds, so one boot
 * shoots four), review the results, and save the ones you keep.
 *
 * Phases: 'select' -> 'capturing' -> 'review'. Streams capture_progress /
 * capture_batch_complete / capture_error over a short-lived socket, like
 * useInGameTest.
 */
import { useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../config'
import { playSound } from '../utils/sounds'

// DAS stage code -> storage folder (the batch endpoint needs the folder).
const CODE_FOLDER = {
  GrOp: 'dreamland', GrPs: 'pokemon_stadium', GrSt: 'yoshis_story',
  GrNBa: 'battlefield', GrIz: 'fountain_of_dreams', GrNLa: 'final_destination',
}

const keyOf = (v) => `${v.stageCode}:${v.id}`

function dataUriToBlob(uri) {
  const [head, b64] = uri.split(',')
  const mime = (head.match(/data:(.*?);/) || [])[1] || 'image/png'
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return new Blob([bytes], { type: mime })
}

export function useBulkStageCapture({ onSaved } = {}) {
  const [phase, setPhase] = useState('select')        // select | capturing | review
  const [variants, setVariants] = useState([])        // all vault DAS variants
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(() => new Set())  // keys chosen to capture
  const [progress, setProgress] = useState(null)      // { percentage, message }
  const [results, setResults] = useState([])          // [{..., ok, screenshot, reason}]
  const [keep, setKeep] = useState(() => new Set())   // variantIds to save (review)
  const [saving, setSaving] = useState(false)
  const socketRef = useRef(null)

  const cleanupSocket = () => {
    if (socketRef.current) {
      try { socketRef.current.disconnect() } catch (e) { /* ignore */ }
      socketRef.current = null
    }
  }

  const reset = () => {
    cleanupSocket()
    setPhase('select'); setProgress(null); setResults([]); setKeep(new Set())
    setSelected(new Set()); setError(null); setSaving(false)
  }

  const loadVariants = async () => {
    setLoading(true); setError(null)
    try {
      const res = await fetch(`${API_URL}/das/storage/variants`)
      const data = await res.json()
      if (data.success) setVariants(data.variants || [])
      else setError(data.error || 'Failed to load variants')
    } catch (err) {
      setError(`Failed to load variants: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const toggle = (v) => {
    const k = keyOf(v)
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(k) ? next.delete(k) : next.add(k)
      return next
    })
  }
  const setMany = (vs, on) => setSelected((prev) => {
    const next = new Set(prev)
    vs.forEach((v) => (on ? next.add(keyOf(v)) : next.delete(keyOf(v))))
    return next
  })
  const clearSelection = () => setSelected(new Set())

  const startCapture = async () => {
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    const slippiDolphinPath = localStorage.getItem('slippi_dolphin_path')
    if (!vanillaIsoPath) { setError('No vanilla Melee ISO path set. Set it in Settings first.'); return }
    if (!slippiDolphinPath) { setError('No Slippi Dolphin path set. Set it in Settings first.'); return }

    const chosen = variants.filter((v) => selected.has(keyOf(v)))
    if (!chosen.length) return
    const payload = chosen.map((v) => ({
      stageCode: v.stageCode,
      stageFolder: CODE_FOLDER[v.stageCode],
      variantId: v.id,
      name: v.name,
    }))

    playSound('start')
    setPhase('capturing'); setError(null)
    setProgress({ percentage: 0, message: `Starting capture of ${chosen.length}…` })

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('capture_progress', (d) => setProgress(d))
    socket.on('capture_batch_complete', (d) => {
      const rs = d.results || []
      setResults(rs)
      // default: keep every successful shot (the user can deselect before saving)
      setKeep(new Set(rs.filter((r) => r.ok && r.screenshot).map((r) => r.variantId)))
      setPhase('review')
      playSound(d.captured ? 'achievement' : 'error')
      cleanupSocket()
    })
    socket.on('capture_error', (d) => {
      setError(d.error || 'Bulk capture failed')
      setPhase('select')
      playSound('error')
      cleanupSocket()
    })

    try {
      const res = await fetch(`${API_URL}/test-in-game/capture-stage-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variants: payload, vanillaIsoPath, slippiDolphinPath }),
      })
      const data = await res.json()
      if (!data.success) {
        setError(data.error || 'Failed to start bulk capture')
        setPhase('select'); playSound('error'); cleanupSocket()
      }
    } catch (err) {
      setError(`Failed to start bulk capture: ${err.message}`)
      setPhase('select'); playSound('error'); cleanupSocket()
    }
  }

  const toggleKeep = (variantId) => setKeep((prev) => {
    const next = new Set(prev)
    next.has(variantId) ? next.delete(variantId) : next.add(variantId)
    return next
  })

  const saveKept = async () => {
    const toSave = results.filter((r) => r.ok && r.screenshot && keep.has(r.variantId))
    if (!toSave.length) return
    setSaving(true); setError(null)
    let saved = 0
    for (const r of toSave) {
      try {
        const fd = new FormData()
        fd.append('stageFolder', r.stageFolder)
        fd.append('variantId', r.variantId)
        fd.append('screenshot', dataUriToBlob(r.screenshot), `${r.variantId}.png`)
        const res = await fetch(`${API_URL}/storage/stages/update-screenshot`, { method: 'POST', body: fd })
        const data = await res.json()
        if (data.success) saved++
      } catch (e) { /* keep going; reported via count */ }
    }
    setSaving(false)
    playSound(saved ? 'achievement' : 'error')
    if (onSaved) onSaved(saved)
    return saved
  }

  return {
    phase, variants, loading, error,
    selected, toggle, setMany, clearSelection, keyOf,
    progress, results, keep, toggleKeep, saving,
    loadVariants, startCapture, saveKept, reset, setError,
  }
}
