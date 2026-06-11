/**
 * useAiEngine - status + model catalog for the AI Studio settings hub.
 *
 * `ready` is the setup gate: an OpenRouter key (backend env OR localStorage)
 * or at least one downloaded+enabled local model unlocks the studios.
 */
import { useCallback, useEffect, useState } from 'react'

export default function useAiEngine(API_URL) {
  const [status, setStatus] = useState(null)
  const [models, setModels] = useState(null)
  const [loadError, setLoadError] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([
        fetch(`${API_URL}/ai-engine/status`).then((r) => r.json()),
        fetch(`${API_URL}/ai-engine/models`).then((r) => r.json()),
      ])
      if (s.success) setStatus(s)
      if (m.success) setModels(m)
      setLoadError(!s.success && !m.success)
    } catch {
      setLoadError(true)
    }
  }, [API_URL])

  useEffect(() => { refresh() }, [refresh])

  const hasLocalKey = Boolean(localStorage.getItem('openrouter_api_key'))
  const hasKey = Boolean(status?.hasBackendKey) || hasLocalKey
  const ready = Boolean(status && (hasKey || status.localModelReady))

  return { status, models, refresh, ready, hasKey, hasLocalKey, loadError }
}

export function fmtBytes(bytes) {
  if (!bytes) return '0 B'
  const gb = bytes / 1024 ** 3
  if (gb >= 0.1) return `${gb.toFixed(1)} GB`
  return `${(bytes / 1024 ** 2).toFixed(0)} MB`
}

export function fmtAgo(ts) {
  if (!ts) return '—'
  const days = (Date.now() / 1000 - ts) / 86400
  if (days < 1 / 24) return 'just now'
  if (days < 1) return `${Math.round(days * 24)}h ago`
  if (days < 30) return `${Math.round(days)}d ago`
  return `${Math.round(days / 30)}mo ago`
}
