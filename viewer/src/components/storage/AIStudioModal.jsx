import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../../config'
import { playSound } from '../../utils/sounds'
import useAiStudioSetup, { ResolutionNotice, SetupGate, autoOptionLabel } from './useAiStudioSetup'

const PLANNERS = [
  { id: 'openai/gpt-5-mini', label: 'GPT-5 Mini (recommended)' },
  { id: 'google/gemini-3-flash-preview', label: 'Gemini 3 Flash' },
  { id: 'anthropic/claude-haiku-4.5', label: 'Claude Haiku 4.5' },
]

const TASK_KINDS = ['material']

/**
 * AI Skin Studio: describe a theme, an AI model plans the skin, the lab
 * executes it live, and you get a front/back/CSP preview to save or discard.
 */
export default function AIStudioModal({ show, character, onClose, onSaved }) {
  const [theme, setTheme] = useState('')
  const [planner, setPlanner] = useState(PLANNERS[0].id)
  // '' = Auto: the backend's tier resolver picks per task
  const [imageModel, setImageModel] = useState(
    localStorage.getItem('ai_studio_image_model') || '')
  const { ready, options, localPlanners, resolution, autoResolution, resolveFor } =
    useAiStudioSetup(show, TASK_KINDS)
  const [phase, setPhase] = useState('form')        // form | running | preview | saving
  const [status, setStatus] = useState(null)
  const [sheet, setSheet] = useState(null)
  const [skinName, setSkinName] = useState('')
  const [steps, setSteps] = useState([])
  const [costInfo, setCostInfo] = useState(null)
  const [assessment, setAssessment] = useState(null)
  const [error, setError] = useState(null)
  const socketRef = useRef(null)

  const cleanupSocket = () => {
    if (socketRef.current) {
      socketRef.current.disconnect()
      socketRef.current = null
    }
  }

  const closeSession = () => {
    fetch(`${API_URL}/skin-lab/close`, { method: 'POST' }).catch(() => {})
  }

  useEffect(() => {
    if (!show) {
      cleanupSocket()
      setPhase('form')
      setStatus(null)
      setSheet(null)
      setError(null)
    }
    return cleanupSocket
  }, [show])

  // drop a stale stored pick (model deleted/disabled since) back to Auto
  useEffect(() => {
    if (show && options.length && imageModel
        && !options.some((o) => o.value === imageModel)) {
      setImageModel('')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, options])

  // preview what each task will actually run on (escalation notice)
  useEffect(() => {
    if (show && ready) resolveFor(imageModel)
  }, [show, ready, imageModel, resolveFor])

  if (!show) return null

  const run = async () => {
    if (!theme.trim()) return
    playSound('start')
    setPhase('running')
    setError(null)
    setStatus({ percentage: 0, message: 'Starting…' })

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('ailab_progress', (d) => setStatus(d))
    socket.on('ailab_complete', (d) => {
      setSheet(d.sheet)
      setSkinName(d.skinName || theme)
      setSteps(d.steps || [])
      setCostInfo({ cost: d.estCostUsd, generation: d.generation || [] })
      setAssessment(d.assessment || null)
      setPhase('preview')
      playSound('achievement')
      cleanupSocket()
    })
    socket.on('ailab_error', (d) => {
      setError(d.error || 'AI Studio failed')
      setPhase('form')
      playSound('error')
      cleanupSocket()
    })

    try {
      const res = await fetch(`${API_URL}/skin-lab/ai-create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          theme: theme.trim(),
          plannerModel: planner,
          // Auto ('') sends neither — the backend's tier resolver picks
          imageProvider: options.find((o) => o.value === imageModel)?.provider,
          imageModel: imageModel || undefined,
          openrouterKey: localStorage.getItem('openrouter_api_key') || undefined,
        }),
      })
      const data = await res.json()
      if (!data.success) {
        setError(data.error || 'Could not start the AI Studio')
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
      const res = await fetch(`${API_URL}/skin-lab/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: skinName.trim() || theme.trim() }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'save failed')
      playSound('achievement')
      closeSession()
      onSaved?.()
      onClose()
    } catch (err) {
      setError(`Save failed: ${err.message}`)
      setPhase('preview')
      playSound('error')
    }
  }

  const discard = () => {
    closeSession()
    setPhase('form')
    setSheet(null)
  }

  const handleClose = () => {
    if (phase === 'running') return   // let it finish or fail
    if (phase === 'preview') closeSession()
    onClose()
  }

  return (
    <div className="ai-studio-overlay" onClick={handleClose}>
      <div className="ai-studio-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ai-studio-header">
          <h3>✨ AI Skin Studio — {character}</h3>
          <button className="ai-studio-close" onClick={handleClose}>×</button>
        </div>

        {phase === 'form' && ready === false && <SetupGate onClose={onClose} />}

        {phase === 'form' && ready !== false && (
          <div className="ai-studio-form">
            <label className="ai-studio-label">Describe the skin you want</label>
            <textarea
              className="ai-studio-theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder={'e.g. "royal crusader: polished steel plate armor, deep crimson cloth, gold trim"'}
              rows={3}
              autoFocus
            />
            <label className="ai-studio-label">Planner model</label>
            <select className="ai-studio-planner" value={planner}
                    onChange={(e) => setPlanner(e.target.value)}>
              {PLANNERS.map((p) => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
              {localPlanners.map((p) => (
                <option key={p.id} value={p.id}>{p.label}</option>
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
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
            <ResolutionNotice resolution={resolution} />
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
            <img className="ai-studio-sheet" src={sheet} alt="skin preview" />
            {steps.length > 0 && (
              <div className="ai-studio-steps">
                {steps.map((s, i) => (
                  <span key={i} className="ai-studio-step">
                    {s.op}:{s.region}
                  </span>
                ))}
              </div>
            )}
            {assessment && (
              <div className="ai-studio-progress-message">“{assessment}”</div>
            )}
            {costInfo && costInfo.generation.length > 0 && (
              <div className="ai-studio-genlog">
                {costInfo.generation.map((g, i) => (
                  <div key={i} className="ai-studio-progress-message">
                    material {i + 1}: {g.model}
                    {g.seconds != null ? ` — ${g.seconds}s` : ''}
                    {g.cached ? ' — cached (free)'
                      : g.estCostUsd > 0 ? ` — ~${Math.round(g.estCostUsd * 100)}¢`
                        : ' — free (local)'}
                    {g.escalated ? ' — escalated for scene quality' : ''}
                  </div>
                ))}
                <div className="ai-studio-progress-message">
                  total: {costInfo.cost > 0 ? `~$${costInfo.cost.toFixed(2)}` : 'free'}
                  {' · '}
                  {costInfo.generation.reduce((s, g) => s + (g.seconds || 0), 0).toFixed(0)}s generating
                </div>
              </div>
            )}
            <input
              className="ai-studio-name"
              value={skinName}
              onChange={(e) => setSkinName(e.target.value)}
              placeholder="Skin name"
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
