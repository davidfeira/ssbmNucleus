/**
 * LocalPlannerCard - local planner LLMs via Ollama: the text model that
 * PLANS the skins (and, if vision-capable like gemma3:4b, reviews the
 * results). With one installed, planning needs no API key — combined with
 * local image models the studios run fully offline.
 */
import { useCallback, useEffect, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'
import { fmtBytes } from './useAiEngine'

export default function LocalPlannerCard({ API_URL, socket, onChanged }) {
  const [info, setInfo] = useState(null)
  const [pull, setPull] = useState(null)   // {model, completed, total, status}
  const [rtInstall, setRtInstall] = useState(null)   // {message, percentage}
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    fetch(`${API_URL}/ai-engine/planners`)
      .then((r) => r.json())
      .then((d) => { if (d.success) setInfo(d) })
      .catch(() => {})
  }, [API_URL])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!socket) return
    const onTick = (d) => setPull(d)
    const onDone = () => {
      setPull(null)
      playSound('achievement')
      load()
      onChanged?.()
    }
    const onErr = (d) => {
      setPull(null)
      setError(d.error || 'pull failed')
      playSound('error')
    }
    const onRtTick = (d) => setRtInstall(d)
    const onRtDone = () => {
      setRtInstall(null)
      playSound('achievement')
      load()
      onChanged?.()
    }
    const onRtErr = (d) => {
      setRtInstall(null)
      setError(d.error || 'Ollama install failed')
      playSound('error')
    }
    socket.on('aiengine_planner_pull', onTick)
    socket.on('aiengine_planner_pull_complete', onDone)
    socket.on('aiengine_planner_pull_error', onErr)
    socket.on('aiengine_ollama_progress', onRtTick)
    socket.on('aiengine_ollama_complete', onRtDone)
    socket.on('aiengine_ollama_error', onRtErr)
    return () => {
      socket.off('aiengine_planner_pull', onTick)
      socket.off('aiengine_planner_pull_complete', onDone)
      socket.off('aiengine_planner_pull_error', onErr)
      socket.off('aiengine_ollama_progress', onRtTick)
      socket.off('aiengine_ollama_complete', onRtDone)
      socket.off('aiengine_ollama_error', onRtErr)
    }
  }, [socket, load, onChanged])

  const installRuntime = async () => {
    setError(null)
    playSound('start')
    setRtInstall({ message: 'starting…' })
    try {
      const res = await fetch(`${API_URL}/ai-engine/planners/install-runtime`,
                              { method: 'POST' })
      const d = await res.json()
      if (!d.success) {
        setRtInstall(null)
        setError(d.error || 'could not start the install')
      }
    } catch (err) {
      setRtInstall(null)
      setError(err.message)
    }
  }

  const startPull = async (name) => {
    setError(null)
    playSound('start')
    setPull({ model: name, status: 'starting…' })
    try {
      const res = await fetch(`${API_URL}/ai-engine/planners/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: name }),
      })
      const d = await res.json()
      if (!d.success) {
        setPull(null)
        setError(d.error || 'could not start the pull')
      }
    } catch (err) {
      setPull(null)
      setError(err.message)
    }
  }

  const remove = async (name) => {
    setError(null)
    try {
      const res = await fetch(`${API_URL}/ai-engine/planners/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: name }),
      })
      const d = await res.json()
      if (d.success) {
        playSound('boop')
        load()
        onChanged?.()
      } else {
        setError(d.error || 'delete failed')
      }
    } catch (err) {
      setError(err.message)
    }
  }

  if (!info) return null
  const rec = info.recommended
  const hasRec = (info.local || []).some((m) => m.name === rec?.name)

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        Local planner LLM
        {info.ollamaAvailable
          ? <span className="aistudio-badge good">Ollama running</span>
          : <span className="aistudio-badge muted">Ollama not found</span>}
      </div>
      <p className="section-description">
        The text model that plans the skins. With one installed, planning is
        free and offline — no API key needed.
      </p>

      {!info.ollamaAvailable ? (
        rtInstall || info.bundled?.installing ? (
          <div className="aistudio-progress">
            <div className="ai-studio-progress-bar">
              <div
                className={`ai-studio-progress-fill${rtInstall?.percentage == null ? ' indeterminate' : ''}`}
                style={{ width: `${rtInstall?.percentage ?? 100}%` }}
              />
            </div>
            <div className="ai-studio-progress-message">
              {rtInstall?.message || 'installing Ollama…'}
            </div>
          </div>
        ) : (
          <>
            {info.bundled?.supported && (
              <div className="aistudio-model-actions">
                <button className="iso-browse-button" onMouseEnter={playHoverSound}
                        onClick={installRuntime}>
                  Install bundled Ollama (~1.2 GB)
                </button>
                <span className="aistudio-row-hint">
                  self-contained — managed by the app
                </span>
              </div>
            )}
            <div className="aistudio-callout warning">
              No Ollama server found.
              {info.bundled?.supported
                ? ' Use the one-click install above, or '
                : ' '}
              install it yourself from ollama.com, then{' '}
              <button className="aistudio-linkbtn" onClick={load}>re-check</button>.
            </div>
          </>
        )
      ) : (
        <>
          {(info.local || []).map((m) => (
            <div key={m.name} className="aistudio-row">
              <div className="aistudio-row-head" style={{ cursor: 'default' }}>
                <span className="aistudio-dot on" />
                <span className="aistudio-row-name">
                  {m.name}
                  {m.name === rec?.name ? ' — recommended' : ''}
                </span>
                <span className="aistudio-row-hint">{fmtBytes(m.sizeBytes)}</span>
                <button className="iso-browse-button danger"
                        onMouseEnter={playHoverSound}
                        onClick={() => remove(m.name)}>
                  Delete
                </button>
              </div>
            </div>
          ))}

          {pull ? (
            <div className="aistudio-progress">
              <div className="ai-studio-progress-bar">
                <div
                  className="ai-studio-progress-fill"
                  style={{
                    width: pull.total
                      ? `${Math.round(100 * (pull.completed || 0) / pull.total)}%`
                      : '100%',
                  }}
                />
              </div>
              <div className="ai-studio-progress-message">
                {pull.model}: {pull.total
                  ? `${fmtBytes(pull.completed || 0)} / ${fmtBytes(pull.total)}`
                  : (pull.status || 'pulling…')}
              </div>
            </div>
          ) : !hasRec && rec && (
            <div className="aistudio-model-actions">
              <button className="iso-browse-button" onMouseEnter={playHoverSound}
                      onClick={() => startPull(rec.name)}>
                Get {rec.name} (~{rec.sizeGb} GB)
              </button>
              <span className="aistudio-row-hint">{rec.blurb}</span>
            </div>
          )}
        </>
      )}
      {error && <div className="aistudio-callout danger">{error}</div>}
    </div>
  )
}
