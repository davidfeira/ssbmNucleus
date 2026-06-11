import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../../config'
import { playSound } from '../../utils/sounds'

const PLANNERS = [
  { id: 'openai/gpt-5-mini', label: 'GPT-5 Mini (recommended)' },
  { id: 'google/gemini-3-flash-preview', label: 'Gemini 3 Flash' },
  { id: 'anthropic/claude-haiku-4.5', label: 'Claude Haiku 4.5' },
]

const IMAGE_MODELS = [
  { provider: 'openrouter', model: 'google/gemini-2.5-flash-image',
    label: 'Nano Banana — API, best quality (~3¢/image)' },
  { provider: 'assetfarm', model: 'sd-turbo',
    label: 'SD-Turbo — local GPU, free & fast' },
  { provider: 'assetfarm', model: 'flux-klein-4b',
    label: 'FLUX Klein — local GPU, free, sharper (slower)' },
  { provider: 'assetfarm', model: 'z-image-turbo',
    label: 'Z-Image Turbo — local GPU, free, high quality (slowest)' },
]

/**
 * AI Stage Studio: describe a theme, an AI model plans the DAS alt, the
 * pipeline retextures the stage and captures a real in-game screenshot to
 * save or discard. Slower than the character studio (builds a test ISO and
 * boots Dolphin for the preview).
 */
export default function StageAIStudioModal({ show, stage, onClose, onSaved }) {
  const [theme, setTheme] = useState('')
  const [planner, setPlanner] = useState(PLANNERS[0].id)
  const [imageModel, setImageModel] = useState(
    localStorage.getItem('ai_studio_image_model') || IMAGE_MODELS[0].model)
  const [phase, setPhase] = useState('form')        // form | running | preview | saving
  const [status, setStatus] = useState(null)
  const [screenshot, setScreenshot] = useState(null)
  const [skinName, setSkinName] = useState('')
  const [steps, setSteps] = useState([])
  const [costInfo, setCostInfo] = useState(null)
  const [error, setError] = useState(null)
  const socketRef = useRef(null)

  const cleanupSocket = () => {
    if (socketRef.current) {
      socketRef.current.disconnect()
      socketRef.current = null
    }
  }

  const discardPending = () => {
    fetch(`${API_URL}/stage-lab/discard`, { method: 'POST' }).catch(() => {})
  }

  useEffect(() => {
    if (!show) {
      cleanupSocket()
      setPhase('form')
      setStatus(null)
      setScreenshot(null)
      setError(null)
    }
    return cleanupSocket
  }, [show])

  if (!show) return null

  const run = async () => {
    if (!theme.trim()) return
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    const slippiDolphinPath = localStorage.getItem('slippi_dolphin_path')
    if (!vanillaIsoPath || !slippiDolphinPath) {
      setError('Set the vanilla ISO and Slippi Dolphin paths in Settings first.')
      return
    }
    playSound('start')
    setPhase('running')
    setError(null)
    setStatus({ percentage: 0, message: 'Starting…' })

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('stagelab_progress', (d) => setStatus(d))
    socket.on('stagelab_complete', (d) => {
      setScreenshot(d.screenshot)
      setSkinName(d.skinName || theme)
      setSteps(d.steps || [])
      setCostInfo({ cost: d.estCostUsd, generation: d.generation || [] })
      setPhase('preview')
      playSound('achievement')
      cleanupSocket()
    })
    socket.on('stagelab_error', (d) => {
      setError(d.error || 'AI Stage Studio failed')
      setPhase('form')
      playSound('error')
      cleanupSocket()
    })

    try {
      const res = await fetch(`${API_URL}/stage-lab/ai-create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageCode: stage.code,
          theme: theme.trim(),
          plannerModel: planner,
          imageProvider: IMAGE_MODELS.find((m) => m.model === imageModel)?.provider,
          imageModel,
          openrouterKey: localStorage.getItem('openrouter_api_key') || undefined,
          vanillaIsoPath,
          slippiDolphinPath,
        }),
      })
      const data = await res.json()
      if (!data.success) {
        setError(data.error || 'Could not start the AI Stage Studio')
        setPhase('form')
        cleanupSocket()
      }
    } catch (err) {
      setError(`Could not start: ${err.message}`)
      setPhase('form')
      cleanupSocket()
    }
  }

  const save = async () => {
    setPhase('saving')
    try {
      const res = await fetch(`${API_URL}/stage-lab/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: skinName.trim() }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'save failed')
      playSound('achievement')
      onSaved?.()
      onClose()
    } catch (err) {
      setError(`Save failed: ${err.message}`)
      setPhase('preview')
      playSound('error')
    }
  }

  const discard = () => {
    discardPending()
    setPhase('form')
    setScreenshot(null)
  }

  const handleClose = () => {
    if (phase === 'running') return
    if (phase === 'preview') discardPending()
    onClose()
  }

  return (
    <div className="ai-studio-overlay" onClick={handleClose}>
      <div className="ai-studio-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ai-studio-header">
          <h3>✨ AI Stage Studio — {stage.name}</h3>
          <button className="ai-studio-close" onClick={handleClose}>×</button>
        </div>

        {phase === 'form' && (
          <div className="ai-studio-form">
            <label className="ai-studio-label">Describe the stage alt you want</label>
            <textarea
              className="ai-studio-theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder={'e.g. "molten core: volcanic basalt, glowing lava cracks, apocalyptic ember sky"'}
              rows={3}
              autoFocus
            />
            <label className="ai-studio-label">Planner model</label>
            <select className="ai-studio-planner" value={planner}
                    onChange={(e) => setPlanner(e.target.value)}>
              {PLANNERS.map((p) => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
            <label className="ai-studio-label">Image model (materials)</label>
            <select className="ai-studio-planner" value={imageModel}
                    onChange={(e) => {
                      setImageModel(e.target.value)
                      localStorage.setItem('ai_studio_image_model', e.target.value)
                    }}>
              {IMAGE_MODELS.map((m) => (
                <option key={m.model} value={m.model}>{m.label}</option>
              ))}
            </select>
            <div className="ai-studio-progress-message">
              The preview is a real in-game screenshot — expect a few minutes.
            </div>
            {error && <div className="ai-studio-error">{error}</div>}
            <div className="ai-studio-actions">
              <button className="ai-studio-btn primary" disabled={!theme.trim()} onClick={run}>
                Generate
              </button>
              <button className="ai-studio-btn" onClick={handleClose}>Cancel</button>
            </div>
          </div>
        )}

        {phase === 'running' && (
          <div className="ai-studio-progress">
            <div className="ai-studio-progress-bar">
              <div className="ai-studio-progress-fill"
                   style={{ width: `${status?.percentage ?? 0}%` }} />
            </div>
            <div className="ai-studio-progress-message">{status?.message}</div>
          </div>
        )}

        {(phase === 'preview' || phase === 'saving') && (
          <div className="ai-studio-preview">
            <img className="ai-studio-sheet" src={screenshot} alt="stage preview" />
            {steps.length > 0 && (
              <div className="ai-studio-steps">
                {steps.map((s, i) => (
                  <span key={i} className="ai-studio-step">
                    {s.op}{s.region ? `:${s.region}` : ''}
                  </span>
                ))}
              </div>
            )}
            {costInfo && (
              <div className="ai-studio-progress-message">
                {costInfo.generation.length} material(s) — {
                  costInfo.cost > 0
                    ? `~$${costInfo.cost.toFixed(2)} (${costInfo.generation[0]?.model})`
                    : `free (local${costInfo.generation[0]?.model ? `, ${costInfo.generation[0].model}` : ''})`
                }
              </div>
            )}
            <input
              className="ai-studio-name"
              value={skinName}
              onChange={(e) => setSkinName(e.target.value)}
              placeholder="Variant name"
            />
            {error && <div className="ai-studio-error">{error}</div>}
            <div className="ai-studio-actions">
              <button className="ai-studio-btn primary" disabled={phase === 'saving' || !skinName.trim()}
                      onClick={save}>
                {phase === 'saving' ? 'Saving…' : 'Save to Vault'}
              </button>
              <button className="ai-studio-btn" disabled={phase === 'saving'} onClick={discard}>
                Discard & Retry
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
