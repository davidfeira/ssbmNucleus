/**
 * EngineInstallCard - install/repair the managed local-generation engine
 * (private Python + torch + diffusers). Streams progress over the shared
 * settings socket (aiengine_install_* events).
 */
import { useEffect, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'

export default function EngineInstallCard({ API_URL, status, socket, onChanged }) {
  const [variant, setVariant] = useState('auto')
  const [progress, setProgress] = useState(null)   // {phase, message, percentage}
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!socket) return
    const onProgress = (d) => { setProgress(d); setError(null) }
    const onComplete = () => {
      setProgress(null)
      playSound('achievement')
      onChanged?.()
    }
    const onError = (d) => {
      setProgress(null)
      setError(d.error || 'install failed')
      playSound('error')
      onChanged?.()
    }
    socket.on('aiengine_install_progress', onProgress)
    socket.on('aiengine_install_complete', onComplete)
    socket.on('aiengine_install_error', onError)
    return () => {
      socket.off('aiengine_install_progress', onProgress)
      socket.off('aiengine_install_complete', onComplete)
      socket.off('aiengine_install_error', onError)
    }
  }, [socket, onChanged])

  if (!status) return null
  const engine = status.engine || {}
  const installing = Boolean(progress) || status.installState?.installing
  const installedOk = engine.installed && engine.ok
  const staleError = !installing && (error || status.installState?.error)
  const hasGpu = Boolean(status.hardware?.gpu)

  const install = async () => {
    setError(null)
    setProgress({ phase: 'start', message: 'Starting install…' })
    playSound('start')
    try {
      const res = await fetch(`${API_URL}/ai-engine/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(variant === 'auto' ? {} : { variant }),
      })
      const data = await res.json()
      if (!data.success) {
        setProgress(null)
        setError(data.error || 'could not start the install')
      }
    } catch (err) {
      setProgress(null)
      setError(`could not start: ${err.message}`)
    }
  }

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        Local generation engine
        {installedOk && (
          <span className="aistudio-badge good">
            ready{engine.cuda ? ' · CUDA' : ' · CPU'}
          </span>
        )}
        {!engine.installed && !installing && (
          <span className="aistudio-badge muted">not installed</span>
        )}
      </div>
      <p className="section-description">
        Runs the free local image models. One-time install
        (~3&nbsp;GB: Python + PyTorch + diffusers); model weights are
        downloaded separately below.
        {!engine.managed && engine.installed && (
          <span className="path-hint"><br />Using NUCLEUS_AIENGINE_PYTHON: {engine.python}</span>
        )}
      </p>

      {installing ? (
        <div className="aistudio-progress">
          <div className="ai-studio-progress-bar">
            <div
              className={`ai-studio-progress-fill${progress?.percentage == null ? ' indeterminate' : ''}`}
              style={{ width: `${progress?.percentage ?? 100}%` }}
            />
          </div>
          <div className="ai-studio-progress-message">
            {progress?.phase ? `[${progress.phase}] ` : ''}{progress?.message || 'installing…'}
          </div>
        </div>
      ) : !installedOk && (
        <div className="iso-path-container">
          <select
            className="ai-studio-planner"
            value={variant}
            onChange={(e) => setVariant(e.target.value)}
          >
            <option value="auto">
              Auto{hasGpu ? ' (CUDA — GPU detected)' : ' (CPU — no GPU detected)'}
            </option>
            <option value="cuda">CUDA (NVIDIA GPU)</option>
            <option value="cpu">CPU only (slow)</option>
          </select>
          <button className="iso-browse-button" onMouseEnter={playHoverSound}
                  onClick={install}>
            {staleError ? 'Resume install' : 'Install engine'}
          </button>
        </div>
      )}

      {staleError && (
        <div className="aistudio-callout danger">install failed: {staleError}</div>
      )}
    </div>
  )
}
