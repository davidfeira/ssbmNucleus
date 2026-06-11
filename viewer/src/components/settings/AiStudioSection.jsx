/**
 * AiStudioSection - the AI Studio setup & management hub.
 *
 * Everything the studios need lives here: detected hardware, the managed
 * local engine install, the model catalog (download / enable / delete with
 * spec recommendations), the OpenRouter key, tier->model routing, and
 * measured generation stats. The studios stay greyed out until the user has
 * either an OpenRouter key or a downloaded local model.
 */
import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { BACKEND_URL } from '../../config'
import './aistudio/AiStudio.css'
import EngineInstallCard from './aistudio/EngineInstallCard'
import HardwareCard from './aistudio/HardwareCard'
import ModelCatalog from './aistudio/ModelCatalog'
import OpenRouterKeyCard from './aistudio/OpenRouterKeyCard'
import TierRoutingCard from './aistudio/TierRoutingCard'
import UsageStatsCard from './aistudio/UsageStatsCard'
import useAiEngine from './aistudio/useAiEngine'

export default function AiStudioSection({ API_URL }) {
  const [enabled, setEnabled] = useState(false)
  const { status, models, refresh, ready, hasKey, loadError } = useAiEngine(API_URL)
  const [socket, setSocket] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const socketRef = useRef(null)

  useEffect(() => {
    fetch(`${API_URL}/skin-lab/ai-status`)
      .then((r) => r.json())
      .then((d) => setEnabled(Boolean(d.enabled)))
      .catch(() => setEnabled(false))
  }, [API_URL])

  // one shared socket for install + download progress events
  useEffect(() => {
    if (!enabled) return undefined
    const s = io(BACKEND_URL)
    socketRef.current = s
    setSocket(s)
    return () => {
      s.disconnect()
      socketRef.current = null
    }
  }, [enabled])

  if (!enabled) return null

  const onChanged = () => {
    refresh()
    setRefreshKey((k) => k + 1)
  }

  return (
    <section className="settings-section">
      <h3>AI Studio</h3>
      {status && (
        <div className={`aistudio-setup-banner ${ready ? 'ready' : 'pending'}`}>
          {ready
            ? '✓ AI Studios are unlocked'
            : 'Setup needed — add an OpenRouter key or download a local model to unlock the AI Studios.'}
        </div>
      )}
      {!status && (
        <div className="aistudio-callout warning">
          {loadError
            ? 'Could not load the AI engine status — the backend is running an older version. Restart the app (or the backend process) to pick up the AI Studio setup hub.'
            : 'Loading AI engine status…'}
        </div>
      )}
      <HardwareCard status={status} />
      <OpenRouterKeyCard backendHasKey={Boolean(status?.hasBackendKey)}
                         onChanged={onChanged} />
      <EngineInstallCard API_URL={API_URL} status={status} socket={socket}
                         onChanged={onChanged} />
      <ModelCatalog API_URL={API_URL} models={models} socket={socket}
                    onChanged={onChanged} />
      <TierRoutingCard API_URL={API_URL} status={status} models={models}
                       hasKey={hasKey} onChanged={onChanged} />
      <UsageStatsCard API_URL={API_URL} refreshKey={refreshKey} />
    </section>
  )
}
