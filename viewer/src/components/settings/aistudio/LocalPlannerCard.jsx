/**
 * LocalPlannerCard - local planner LLMs via Ollama: the text model that
 * PLANS the skins (and, if vision-capable like gemma3:4b, reviews the
 * results). With one installed, planning needs no API key — combined with
 * local image models the studios run fully offline.
 */
import { useCallback, useEffect, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'
import { fmtBytes } from './useAiEngine'

const FIT_BADGES = {
  good: { cls: 'good', text: 'should run well' },
  slow: { cls: 'warn', text: 'tight on VRAM - may be slow' },
  insufficient_vram: { cls: 'bad', text: 'not enough VRAM' },
  no_gpu: { cls: 'bad', text: 'needs an NVIDIA GPU' },
  unknown: { cls: 'muted', text: 'VRAM varies by model' },
}

const fmtGb = (gb) => {
  const n = Number(gb)
  if (!Number.isFinite(n) || n <= 0) return null
  return Number.isInteger(n) ? n.toFixed(0) : n.toFixed(1)
}

const plannerFitBadge = (model) => {
  if (!model?.vramGb) return FIT_BADGES.unknown
  return FIT_BADGES[model.fit] || FIT_BADGES.good
}

export default function LocalPlannerCard({ API_URL, socket, onChanged }) {
  const [info, setInfo] = useState(null)
  const [pull, setPull] = useState(null)   // {model, completed, total, status}
  const [rtInstall, setRtInstall] = useState(null)   // {message, percentage}
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)   // model name, accordion-style

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

  const cardShell = (children, badge) => (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        Local planner LLM
        {badge}
      </div>
      <p className="section-description">
        The text model that plans the skins. With one installed, planning is
        free and offline — no API key needed.
      </p>
      {children}
      {error && <div className="aistudio-callout danger">{error}</div>}
    </div>
  )

  // skeleton while /planners loads — same card, no layout pop-in
  if (!info) {
    return cardShell(null,
      <span className="aistudio-badge muted">checking Ollama…</span>)
  }

  const recommendedPlanners = info.recommendedPlanners
    || (info.recommended ? [info.recommended] : [])
  const installedPlannerNames = new Set((info.local || []).map((m) => m.name))
  const missingRecommendedPlanners = recommendedPlanners
    .filter((m) => m?.name && !installedPlannerNames.has(m.name))
  const recommendedFor = (name) => recommendedPlanners.find((m) => m.name === name)
  const stats = info.stats || {}
  const measured = (name) => {
    const s = stats[`ollama:${name}`]
    return s?.avgSeconds != null
      ? `~${Math.round(s.avgSeconds)}s/plan measured (${s.runs} runs)`
      : null
  }
  const speedText = (model) => measured(model.name)
    || (model.speedBlurb ? `${model.speedBlurb} (no runs yet)` : null)
  const toggleRow = (name) => {
    playSound('tick')
    setExpanded(expanded === name ? null : name)
  }
  const pullProgress = pull && (
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
  )
  if (!info.ollamaAvailable) {
    return cardShell(
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
      ),
      <span className="aistudio-badge muted">Ollama not found</span>,
    )
  }

  // mirror the image-model catalog: one slim accordion row per model —
  // status dot / lock, name, compact hint, details + actions in the body
  return cardShell(
    <>
      {(info.local || []).map((m) => {
        const pulling = pull?.model === m.name || m.pulling
        const rec = recommendedFor(m.name)
        const fit = plannerFitBadge(m)
        const vram = fmtGb(m.vramGb)
        const speed = speedText(m)
        return (
          <div key={m.name}
               className={`aistudio-row${expanded === m.name ? ' expanded' : ''}`}>
            <button className="aistudio-row-head" onMouseEnter={playHoverSound}
                    onClick={() => toggleRow(m.name)}>
              {pulling
                ? <span className="aistudio-dot busy" />
                : <span className="aistudio-dot on" />}
              <span className="aistudio-row-name">
                {m.name}{rec ? ` — ${rec.tier || 'recommended'}` : ''}
              </span>
              <span className="aistudio-row-hint">
                unlocked · {fmtBytes(m.sizeBytes)}{vram && ` · ~${vram} GB VRAM`}
              </span>
              <span className="aistudio-row-chevron">
                {expanded === m.name ? '▾' : '▸'}
              </span>
            </button>
            {expanded === m.name && (
              <div className="aistudio-row-body">
                <div className="aistudio-model-head">
                  <span className={`aistudio-badge ${fit.cls}`}>{fit.text}</span>
                  <span className="aistudio-badge good">free · offline</span>
                  {m.vision && <span className="aistudio-badge api">vision review</span>}
                </div>
                <div className="aistudio-model-desc">
                  {m.description || 'Custom Ollama planner model.'}
                </div>
                <div className="aistudio-model-specs">
                  {vram ? <span>needs ~{vram} GB VRAM</span> : <span>VRAM varies by model</span>}
                  <span>{fmtBytes(m.sizeBytes)} on disk</span>
                  {speed && <span>{speed}</span>}
                </div>
                {pulling ? pullProgress : (
                  <div className="aistudio-model-actions">
                    <button className="iso-browse-button danger"
                            onMouseEnter={playHoverSound}
                            onClick={() => remove(m.name)}>
                      Delete ({fmtBytes(m.sizeBytes)})
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}

      {missingRecommendedPlanners.map((rec) => {
        const pulling = pull?.model === rec.name
        const fit = plannerFitBadge(rec)
        const vram = fmtGb(rec.vramGb)
        const disk = fmtGb(rec.diskEstimateGb || rec.sizeGb)
        const speed = speedText(rec)
        return (
          <div
            key={rec.name}
            className={`aistudio-row${expanded === rec.name ? ' expanded' : ''}${pulling ? '' : ' locked'}`}
          >
            <button className="aistudio-row-head" onMouseEnter={playHoverSound}
                    onClick={() => toggleRow(rec.name)}>
              {pulling
                ? <span className="aistudio-dot busy" />
                : <span className="aistudio-lock">🔒</span>}
              <span className="aistudio-row-name">
                {rec.name} — {rec.tier || 'recommended'}
              </span>
              <span className={`aistudio-row-hint${pulling ? '' : ' locked'}`}>
                {pulling
                  ? (pull.total
                    ? `${Math.round(100 * (pull.completed || 0) / pull.total)}%…`
                    : 'starting…')
                  : `not downloaded · ${vram ? `~${vram} GB VRAM` : 'VRAM varies'}`}
              </span>
              <span className="aistudio-row-chevron">
                {expanded === rec.name ? '▾' : '▸'}
              </span>
            </button>
            {expanded === rec.name && (
              <div className="aistudio-row-body">
                <div className="aistudio-model-head">
                  <span className={`aistudio-badge ${fit.cls}`}>{fit.text}</span>
                  <span className="aistudio-badge good">free · offline</span>
                  {rec.vision && <span className="aistudio-badge api">vision review</span>}
                </div>
                <div className="aistudio-model-desc">{rec.description || rec.blurb}</div>
                <div className="aistudio-model-specs">
                  {vram ? <span>needs ~{vram} GB VRAM</span> : <span>VRAM varies by model</span>}
                  {disk && <span>~{disk} GB download</span>}
                  {speed && <span>{speed}</span>}
                </div>
                {pulling ? pullProgress : (
                  <div className="aistudio-model-actions">
                    <button className="iso-browse-button" onMouseEnter={playHoverSound}
                            onClick={() => startPull(rec.name)}>
                      Download{disk ? ` (~${disk} GB)` : ''}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </>,
    <span className="aistudio-badge good">Ollama running</span>,
  )
}
