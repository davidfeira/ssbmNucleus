/**
 * useAiStudioSetup - shared setup/gating + model-picker data for the AI
 * Studio modals.
 *
 * - `ready`: the setup gate (OpenRouter key OR a downloaded local model).
 * - `options`: the live model list for the picker (replaces the old
 *   hardcoded array) — only enabled+downloaded locals and, with a key,
 *   API models. '' (Auto) lets the backend's tier resolver pick.
 * - `resolution`: what each task of this studio will actually use, from
 *   POST /ai-engine/resolve — including escalation notices ("backgrounds
 *   will use Nano Banana — your local model isn't suited for scenes").
 */
import { useCallback, useEffect, useState } from 'react'
import { API_URL } from '../../config'

export default function useAiStudioSetup(show, taskKinds) {
  const [ready, setReady] = useState(null)   // null = probing
  const [options, setOptions] = useState([])
  const [localPlanners, setLocalPlanners] = useState([])
  const [resolution, setResolution] = useState(null)
  const [autoResolution, setAutoResolution] = useState(null)

  const hasLocalKey = Boolean(localStorage.getItem('openrouter_api_key'))

  useEffect(() => {
    if (!show) return
    let cancelled = false
    Promise.all([
      fetch(`${API_URL}/skin-lab/ai-status`).then((r) => r.json()),
      fetch(`${API_URL}/ai-engine/models`).then((r) => r.json()),
      fetch(`${API_URL}/ai-engine/planners`).then((r) => r.json()).catch(() => ({})),
    ]).then(([st, m, p]) => {
      if (cancelled) return
      setReady(Boolean(st.hasKey || hasLocalKey || st.localModelReady))
      if (m.success) {
        const usable = m.models.filter((mm) => (
          mm.kind === 'local'
            ? (mm.downloaded && mm.enabled && !mm.needsEngineUpdate)
            : (st.hasKey || hasLocalKey)))
        setOptions(usable.map((mm) => ({
          value: mm.kind === 'api' ? mm.repoId : mm.id,
          provider: mm.kind === 'api' ? 'openrouter' : 'local',
          label: mm.stats?.avgSeconds != null
            ? `${mm.label} — ~${Math.round(mm.stats.avgSeconds)}s/image`
            : mm.label,
        })))
      }
      // installed Ollama models double as free offline planner LLMs
      setLocalPlanners((p.local || []).map((name) => ({
        id: `ollama:${name}`,
        label: `${name} — local LLM (free, offline)`,
      })))
    }).catch(() => { if (!cancelled) setReady(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  // always know what Auto would pick (even while an explicit model is
  // selected) — feeds the picker's 'Auto — <model>' label only
  useEffect(() => {
    if (!show) return
    fetch(`${API_URL}/ai-engine/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks: taskKinds.map((kind) => ({ kind })),
                             clientHasKey: hasLocalKey }),
    })
      .then((r) => r.json())
      .then((d) => { if (d.success) setAutoResolution(d.tasks) })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  const resolveFor = useCallback((selectedModel) => {
    const tasks = taskKinds.map((kind) => ({
      kind,
      model: selectedModel || undefined,
    }))
    fetch(`${API_URL}/ai-engine/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tasks, clientHasKey: hasLocalKey }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (!d.success) return
        setResolution(d.tasks)
        if (!selectedModel) setAutoResolution(d.tasks)
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskKinds.join(','), hasLocalKey])

  return { ready, options, localPlanners, resolution, autoResolution, resolveFor }
}

const shortName = (label) => (label || '').replace(/\s*\([^)]*\)\s*$/, '')

/** 'Auto — SD-Turbo' / 'Auto — SD-Turbo / scenes: Nano Banana' — shows what
 * the resolver would actually pick for THIS machine's setup. */
export function autoOptionLabel(autoResolution) {
  const ok = (autoResolution || []).filter((t) => !t.error && t.label)
  if (!ok.length) return 'Auto (recommended)'
  const names = [...new Set(ok.map((t) => shortName(t.label)))]
  if (names.length === 1) return `Auto — ${names[0]}`
  const material = ok.find((t) => t.kind === 'material')
  const backdrop = ok.find((t) => t.kind === 'backdrop')
  return `Auto — ${shortName(material?.label)} / scenes: ${shortName(backdrop?.label)}`
}

const TASK_LABELS = {
  material: 'Materials',
  backdrop: 'Backgrounds',
}

/** Per-task "what will run" lines with escalation callouts. */
export function ResolutionNotice({ resolution }) {
  if (!resolution) return null
  return (
    <div className="ai-studio-resolution">
      {resolution.map((t) => (
        <div key={t.kind}
             className={`ai-studio-progress-message${t.escalated || t.error ? ' escalated' : ''}`}>
          {TASK_LABELS[t.kind] || t.kind} → {t.error ? t.error : t.label}
          {t.escalated && t.reason ? ` — ${t.reason}` : ''}
        </div>
      ))}
    </div>
  )
}

/** The greyed-out gate panel shown when setup is incomplete. */
export function SetupGate({ onClose }) {
  return (
    <div className="ai-studio-form ai-studio-gate">
      <div className="ai-studio-gate-icon">🔒</div>
      <div className="ai-studio-gate-text">
        <strong>Set up AI Studio first</strong>
        <p>
          You need either an OpenRouter API key (for API models) or a
          downloaded local model (free, runs on your GPU). Both live in
          Settings → AI Studio.
        </p>
      </div>
      <div className="ai-studio-actions">
        <button
          className="ai-studio-btn primary"
          onClick={() => {
            onClose?.()
            // switches to the Settings tab AND opens the AI Studio popup
            window.dispatchEvent(new CustomEvent('nucleus:open-settings',
              { detail: { section: 'ai-studio' } }))
          }}
        >
          Open AI Studio setup
        </button>
        <button className="ai-studio-btn" onClick={onClose}>Cancel</button>
      </div>
    </div>
  )
}
