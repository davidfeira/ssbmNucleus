/**
 * ModelCatalog - one card per model: recommended specs, a fit badge derived
 * from the detected hardware, measured generation times once telemetry
 * exists, and download / enable / delete management for local models.
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

function ModelCard({ API_URL, model, socket, onChanged }) {
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
  const stats = model.stats
  const speed = stats?.avgSeconds != null
    ? `~${Math.round(stats.avgSeconds)}s/image measured (${stats.runs} runs)`
    : (model.speedBlurb ? `${model.speedBlurb} (no runs yet)` : null)

  return (
    <div className={`aistudio-model${model.enabled ? '' : ' disabled'}`}>
      <div className="aistudio-model-head">
        <span className="aistudio-model-name">{model.label}</span>
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
        {!isLocal && model.requiresKey && <span>needs an OpenRouter key</span>}
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
  )
}

export default function ModelCatalog({ API_URL, models, socket, onChanged }) {
  if (!models) return null
  const local = models.models.filter((m) => m.kind === 'local')
  const api = models.models.filter((m) => m.kind === 'api')

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">Image models</div>
      <p className="section-description">
        Local models run free on your GPU; API models bill per image through
        OpenRouter. Pick what fits your machine — the badges compare each
        model's needs against your hardware.
      </p>
      {local.map((m) => (
        <ModelCard key={m.id} API_URL={API_URL} model={m} socket={socket}
                   onChanged={onChanged} />
      ))}
      {api.map((m) => (
        <ModelCard key={m.id} API_URL={API_URL} model={m} socket={socket}
                   onChanged={onChanged} />
      ))}
      <div className="aistudio-storage-footer">
        {fmtBytes(models.totalDiskBytes)} of model weights ·
        cache: <span className="aistudio-mono">{models.cacheDir}</span>
      </div>
    </div>
  )
}
