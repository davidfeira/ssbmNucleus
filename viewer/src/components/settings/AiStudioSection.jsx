/**
 * AiStudioSection - compact AI Studio status card in Settings.
 *
 * The full setup & management hub (hardware, engine install, model catalog,
 * OpenRouter key, tier routing, usage stats) lives in a popup opened from
 * here — it's too much UI to sit inline on the settings page. The studios'
 * locked-state CTA deep-links into the popup via the
 * 'nucleus:open-settings' event with {section: 'ai-studio'}.
 */
import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { BACKEND_URL } from '../../config'
import { playHoverSound, playSound } from '../../utils/sounds'
import './aistudio/AiStudio.css'
import EngineInstallCard from './aistudio/EngineInstallCard'
import HardwareCard from './aistudio/HardwareCard'
import ModelCatalog from './aistudio/ModelCatalog'
import OpenRouterKeyCard from './aistudio/OpenRouterKeyCard'
import TierRoutingCard from './aistudio/TierRoutingCard'
import UsageStatsCard from './aistudio/UsageStatsCard'
import useAiEngine, { fmtBytes } from './aistudio/useAiEngine'

export default function AiStudioSection({ API_URL }) {
  const [enabled, setEnabled] = useState(false)
  const [showModal, setShowModal] = useState(false)
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

  // the studios' locked-state CTA deep-links into this popup
  useEffect(() => {
    const onOpen = (e) => {
      if (e.detail?.section === 'ai-studio') setShowModal(true)
    }
    window.addEventListener('nucleus:open-settings', onOpen)
    return () => window.removeEventListener('nucleus:open-settings', onOpen)
  }, [])

  // one shared socket for install + download progress (popup lifetime)
  useEffect(() => {
    if (!enabled || !showModal) return undefined
    refresh()
    const s = io(BACKEND_URL)
    socketRef.current = s
    setSocket(s)
    return () => {
      s.disconnect()
      socketRef.current = null
      setSocket(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, showModal])

  if (!enabled) return null

  const onChanged = () => {
    refresh()
    setRefreshKey((k) => k + 1)
  }

  const localReady = (models?.models || [])
    .filter((m) => m.kind === 'local' && m.downloaded && m.enabled)
  const summaryBits = status ? [
    hasKey ? 'API key set' : 'no API key',
    `${localReady.length} local model${localReady.length === 1 ? '' : 's'} ready`,
    status.engine?.installed
      ? (status.engine.ok ? 'engine installed' : 'engine needs repair')
      : 'engine not installed',
    models?.totalDiskBytes ? `${fmtBytes(models.totalDiskBytes)} on disk` : null,
  ].filter(Boolean) : []

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
      <p className="section-description">
        Image models, the local generation engine, your OpenRouter key, and
        generation stats.
        {summaryBits.length > 0 && (
          <span className="path-hint"><br />{summaryBits.join(' · ')}</span>
        )}
      </p>
      <button
        className="iso-browse-button"
        onMouseEnter={playHoverSound}
        onClick={() => { playSound('boop'); setShowModal(true) }}
        disabled={!status}
      >
        Open AI Studio setup
      </button>

      {showModal && (
        <div className="aistudio-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="aistudio-modal" onClick={(e) => e.stopPropagation()}>
            <div className="aistudio-modal-header">
              <h3>✨ AI Studio setup</h3>
              <button className="aistudio-modal-close"
                      onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="aistudio-modal-body">
              {status && (
                <div className={`aistudio-setup-banner ${ready ? 'ready' : 'pending'}`}>
                  {ready
                    ? '✓ AI Studios are unlocked'
                    : 'Pick ONE of the two paths below to unlock the AI Studios.'}
                </div>
              )}
              <HardwareCard status={status} />
              {!ready ? (
                // guided first-run: just the two unlock paths — everything
                // else (full catalog, tier routing, stats) appears once
                // setup completes, so new users aren't buried in options
                <>
                  <div className="aistudio-option-label">
                    Option A — quickest: an OpenRouter API key (pay per image)
                  </div>
                  <OpenRouterKeyCard backendHasKey={Boolean(status?.hasBackendKey)}
                                     onChanged={onChanged} />
                  <div className="aistudio-option-label">
                    Option B — free &amp; offline: install the engine, then
                    download a local model
                  </div>
                  <EngineInstallCard API_URL={API_URL} status={status} socket={socket}
                                     onChanged={onChanged} />
                  <ModelCatalog API_URL={API_URL} models={models} socket={socket}
                                onChanged={onChanged} localOnly />
                </>
              ) : (
                <>
                  <OpenRouterKeyCard backendHasKey={Boolean(status?.hasBackendKey)}
                                     onChanged={onChanged} />
                  <EngineInstallCard API_URL={API_URL} status={status} socket={socket}
                                     onChanged={onChanged} />
                  <ModelCatalog API_URL={API_URL} models={models} socket={socket}
                                onChanged={onChanged} />
                  <TierRoutingCard API_URL={API_URL} status={status} models={models}
                                   hasKey={hasKey} onChanged={onChanged} />
                  <UsageStatsCard API_URL={API_URL} refreshKey={refreshKey} />
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
