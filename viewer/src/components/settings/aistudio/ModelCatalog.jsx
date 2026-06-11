/**
 * ModelCatalog - the image-model list as an ACCORDION: every model is one
 * slim row (status dot, name, compact hint); clicking a row expands it —
 * one at a time — to show specs, fit badge, measured speed, and the
 * download / enable / delete actions. Keeps the list scannable instead of
 * a wall of cards.
 */
import { useEffect, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'
import { fmtBytes } from './useAiEngine'

const FIT_BADGES = {
  good: { cls: 'good', text: 'should run well' },
  slow: { cls: 'warn', text: 'tight on VRAM — may be slow' },
  insufficient_vram: { cls: 'bad', text: 'not enough VRAM' },
  no_gpu: { cls: 'bad', text: 'needs an NVIDIA GPU' },
}

/* a model is UNLOCKED when the studios can actually run it: local needs the
   engine installed AND weights downloaded (and not disabled); api needs a key.
   hasKey folds in the localStorage key — the backend's requiresKey flag only
   knows about its own env var. */
function lockReason(model, engineOk, hasKey) {
  if (model.kind === 'api') return hasKey ? null : 'needs an OpenRouter key'
  if (!engineOk && !model.downloaded) return 'install the engine + download'
  if (!engineOk) return 'install the engine'
  if (!model.downloaded) return model.partial ? 'resume the download' : 'not downloaded yet'
  if (!model.enabled) return 'disabled'
  if (model.needsEngineUpdate) return 'needs engine update'
  return null
}

function compactHint(model, download, locked) {
  if (download) {
    return download.bytesTotal
      ? `${Math.round(100 * download.bytesDone / download.bytesTotal)}%…`
      : 'starting…'
  }
  if (locked) return locked
  if (model.kind === 'api') return `unlocked · ~${Math.round(model.costPerImageUsd * 100)}¢/image`
  return `unlocked · ${fmtBytes(model.sizeOnDiskBytes)}`
}

function ModelRow({ API_URL, model, socket, onChanged, expanded, onToggle,
                    engineOk, hasKey }) {
  const [download, setDownload] = useState(null)   // {bytesDone, bytesTotal}
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!socket) return
    const onProgress = (d) => {
      if (d.modelId === model.id) setDownload(d)
    }
    const onComplete = (d) => {
      if (d.modelId !== model.id) return
      setDownload(null)
      playSound('achievement')
      onChanged?.()
    }
    const onError = (d) => {
      if (d.modelId !== model.id) return
      setDownload(null)
      setError(d.error || 'download failed')
      playSound('error')
      onChanged?.()
    }
    socket.on('aiengine_download_progress', onProgress)
    socket.on('aiengine_download_complete', onComplete)
    socket.on('aiengine_download_error', onError)
    return () => {
      socket.off('aiengine_download_progress', onProgress)
      socket.off('aiengine_download_complete', onComplete)
      socket.off('aiengine_download_error', onError)
    }
  }, [socket, model.id, onChanged])

  const post = async (path, body) => {
    setError(null)
    setBusy(true)
    try {
      const res = await fetch(`${API_URL}/ai-engine/models/${model.id}/${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
      })
      const data = await res.json()
      if (!data.success) setError(data.error || `${path} failed`)
      return data
    } catch (err) {
      setError(err.message)
      return {}
    } finally {
      setBusy(false)
    }
  }

  const startDownload = async () => {
    playSound('start')
    setDownload({ bytesDone: 0, bytesTotal: 0 })
    const data = await post('download')
    if (!data.success) setDownload(null)
  }

  const remove = async () => {
    const data = await post('delete')
    if (data.success) {
      playSound('boop')
      onChanged?.()
    }
  }

  const toggle = async (enabled) => {
    const data = await post('toggle', { enabled })
    if (data.success) onChanged?.()
  }

  const isLocal = model.kind === 'local'
  const fit = FIT_BADGES[model.fit] || FIT_BADGES.good
  const downloading = Boolean(download) || model.downloading
  const locked = downloading ? null : lockReason(model, engineOk, hasKey)
  const stats = model.stats
  const speed = stats?.avgSeconds != null
    ? `~${Math.round(stats.avgSeconds)}s/image measured (${stats.runs} runs)`
    : (model.speedBlurb ? `${model.speedBlurb} (no runs yet)` : null)

  return (
    <div className={`aistudio-row${expanded ? ' expanded' : ''}${locked ? ' locked' : ''}`}>
      <button className="aistudio-row-head" onMouseEnter={playHoverSound}
              onClick={() => { playSound('tick'); onToggle() }}>
        {downloading
          ? <span className="aistudio-dot busy" />
          : locked
            ? <span className="aistudio-lock">🔒</span>
            : <span className="aistudio-dot on" />}
        <span className="aistudio-row-name">{model.label}</span>
        <span className={`aistudio-row-hint${locked ? ' locked' : ''}`}>
          {compactHint(model, download, locked)}
        </span>
        <span className="aistudio-row-chevron">{expanded ? '▾' : '▸'}</span>
      </button>

      {expanded && (
        <div className="aistudio-row-body">
          {isLocal && (
            <div className="aistudio-checklist">
              <div className={engineOk ? 'done' : ''}>
                {engineOk ? '✓' : '○'} local engine installed
                {!engineOk && ' — use the engine card above'}
              </div>
              <div className={model.downloaded ? 'done' : ''}>
                {model.downloaded ? '✓' : '○'} weights downloaded
                {!model.downloaded
                  && ` — ${model.partial ? 'resume below' : `~${model.diskEstimateGb.toFixed(0)} GB, button below`}`}
              </div>
            </div>
          )}
          <div className="aistudio-model-head">
            {isLocal
              ? <span className={`aistudio-badge ${fit.cls}`}>{fit.text}</span>
              : <span className="aistudio-badge api">
                  API · ~{Math.round(model.costPerImageUsd * 100)}¢/image
                </span>}
            {model.needsEngineUpdate && (
              <span className="aistudio-badge bad">needs engine update</span>
            )}
          </div>
          <div className="aistudio-model-desc">{model.description}</div>
          <div className="aistudio-model-specs">
            {isLocal && <span>needs ~{model.vramGb.toFixed(0)} GB VRAM</span>}
            {isLocal && (
              <span>
                {model.downloaded
                  ? `${fmtBytes(model.sizeOnDiskBytes)} on disk`
                  : model.partial
                    ? `incomplete — ${fmtBytes(model.sizeOnDiskBytes)} of ~${model.diskEstimateGb.toFixed(0)} GB`
                    : `~${model.diskEstimateGb.toFixed(0)} GB download`}
              </span>
            )}
            {speed && <span>{speed}</span>}
            {!isLocal && !hasKey && <span>needs an OpenRouter key</span>}
          </div>

          {downloading && (
            <div className="aistudio-progress">
              <div className="ai-studio-progress-bar">
                <div
                  className="ai-studio-progress-fill"
                  style={{
                    width: download?.bytesTotal
                      ? `${Math.round(100 * download.bytesDone / download.bytesTotal)}%`
                      : '100%',
                  }}
                />
              </div>
              <div className="ai-studio-progress-message">
                {download?.bytesTotal
                  ? `${fmtBytes(download.bytesDone)} / ${fmtBytes(download.bytesTotal)}`
                  : 'starting download…'}
              </div>
            </div>
          )}

          {isLocal && !downloading && (
            <div className="aistudio-model-actions">
              {!model.downloaded ? (
                <>
                  <button className="iso-browse-button" disabled={busy}
                          onMouseEnter={playHoverSound} onClick={startDownload}>
                    {model.partial ? 'Resume download' : 'Download'}
                  </button>
                  {model.partial && (
                    <button className="iso-browse-button danger" disabled={busy}
                            onMouseEnter={playHoverSound} onClick={remove}>
                      Delete ({fmtBytes(model.sizeOnDiskBytes)})
                    </button>
                  )}
                </>
              ) : (
                <>
                  <label className="aistudio-toggle">
                    <input type="checkbox" checked={model.enabled}
                           onChange={(e) => toggle(e.target.checked)} />
                    enabled
                  </label>
                  <button className="iso-browse-button danger" disabled={busy}
                          onMouseEnter={playHoverSound} onClick={remove}>
                    Delete ({fmtBytes(model.sizeOnDiskBytes)})
                  </button>
                </>
              )}
            </div>
          )}
          {error && <div className="aistudio-callout danger">{error}</div>}
        </div>
      )}
    </div>
  )
}

export default function ModelCatalog({ API_URL, models, socket, onChanged,
                                       localOnly = false, engineOk = false,
                                       hasKey = false }) {
  const [expandedId, setExpandedId] = useState(null)
  if (!models) return null
  const local = models.models.filter((m) => m.kind === 'local')
  const api = localOnly ? [] : models.models.filter((m) => m.kind === 'api')

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        {localOnly ? 'Local image models' : 'Image models'}
      </div>
      <p className="section-description">
        {localOnly
          ? 'Run free on your GPU. 🔒 models unlock once the engine is installed AND their weights are downloaded. Click a model for details.'
          : 'Local models run free on your GPU (🔒 until the engine is installed and the weights are downloaded); API models unlock with an OpenRouter key. Click a model for details.'}
      </p>
      {[...local, ...api].map((m) => (
        <ModelRow key={m.id} API_URL={API_URL} model={m} socket={socket}
                  onChanged={onChanged} expanded={expandedId === m.id}
                  engineOk={engineOk} hasKey={hasKey}
                  onToggle={() => setExpandedId(expandedId === m.id ? null : m.id)} />
      ))}
      <div className="aistudio-storage-footer">
        {fmtBytes(models.totalDiskBytes)} of model weights ·
        cache: <span className="aistudio-mono">{models.cacheDir}</span>
      </div>
    </div>
  )
}
