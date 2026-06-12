import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../../config'
import { playSound } from '../../utils/sounds'
import useAiStudioSetup, { CostBreakdown, ResolutionNotice, SetupGate,
                           TimeEstimate, autoOptionLabel } from './useAiStudioSetup'

const DEFAULT_PLANNER = 'openai/gpt-5-mini'

// stage alts generate both tile materials AND a coherent backdrop scene —
// the backdrop is 'strong' tier and may escalate to a stronger/paid model
const TASK_KINDS = ['material', 'backdrop']

/**
 * AI Stage Studio: describe a theme, an AI model plans the DAS alt, the
 * pipeline retextures the stage and captures a real in-game screenshot to
 * save or discard. Slower than the character studio (builds a test ISO and
 * boots Dolphin for the preview).
 */
export default function StageAIStudioModal({ show, stage, onClose, onSaved }) {
  const [theme, setTheme] = useState('')
  const [planner, setPlanner] = useState(DEFAULT_PLANNER)
  // '' = Auto: the backend's tier resolver picks per task
  const [imageModel, setImageModel] = useState(
    localStorage.getItem('ai_studio_image_model') || '')
  const { ready, options, planners, resolution, autoResolution, resolveFor } =
    useAiStudioSetup(show, TASK_KINDS)
  const [reviewPass, setReviewPass] = useState(false)
  const [assessment, setAssessment] = useState(null)
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

  // drop a stale stored pick (model deleted/locked since) back to Auto
  useEffect(() => {
    if (show && options.length && imageModel
        && !options.some((o) => o.value === imageModel && !o.locked)) {
      setImageModel('')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, options])

  // preview what materials vs backgrounds will actually run on
  useEffect(() => {
    if (show && ready) resolveFor(imageModel)
  }, [show, ready, imageModel, resolveFor])

  // a locked planner can't run — fall back to the first unlocked one
  useEffect(() => {
    if (!show || !planners.length) return
    const current = planners.find((p) => p.id === planner)
    if (!current || current.locked) {
      const first = planners.find((p) => !p.locked)
      if (first) setPlanner(first.id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, planners])

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
      setCostInfo({ cost: d.estCostUsd, generation: d.generation || [],
                    planning: d.planning || [] })
      setAssessment(d.assessment || null)
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
          // Auto ('') sends neither — the backend's tier resolver picks
          imageProvider: options.find((o) => o.value === imageModel)?.provider,
          imageModel: imageModel || undefined,
          reviewPass,
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

        {phase === 'form' && ready === false && <SetupGate onClose={onClose} />}

        {phase === 'form' && ready !== false && (
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
              {planners.map((p) => (
                <option key={p.id} value={p.id} disabled={p.locked}>
                  {p.locked ? `🔒 ${p.label} — ${p.reason}` : p.label}
                </option>
              ))}
            </select>
            <label className="ai-studio-label">Image model (materials)</label>
            <select className="ai-studio-planner" value={imageModel}
                    onChange={(e) => {
                      setImageModel(e.target.value)
                      localStorage.setItem('ai_studio_image_model', e.target.value)
                    }}>
              <option value="">{autoOptionLabel(autoResolution)}</option>
              {options.map((m) => (
                <option key={m.value} value={m.value} disabled={m.locked}>
                  {m.locked ? `🔒 ${m.label} — ${m.reason}` : m.label}
                </option>
              ))}
            </select>
            <ResolutionNotice resolution={resolution} />
            <TimeEstimate resolution={resolution} stage />
            <label className="ai-studio-label" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="checkbox" checked={reviewPass}
                     onChange={(e) => setReviewPass(e.target.checked)} />
              Review pass — the AI critiques the screenshot and fixes it (adds ~3 min)
            </label>
            <div className="ai-studio-progress-message">
              The preview is a real in-game screenshot — expect a few minutes.
            </div>
            {error && <div className="ai-studio-error">{error}</div>}
            <div className="ai-studio-actions">
              <button className="ai-studio-btn primary"
                      disabled={!theme.trim() || ready === null} onClick={run}>
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
            {assessment && (
              <div className="ai-studio-assessment">“{assessment}”</div>
            )}
            <CostBreakdown costInfo={costInfo} />
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
