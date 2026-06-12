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

// API planner LLMs (OpenRouter text models) — locked without a key
const API_PLANNERS = [
  { id: 'openai/gpt-5-mini', label: 'GPT-5 Mini (recommended)' },
  { id: 'google/gemini-3-flash-preview', label: 'Gemini 3 Flash' },
  { id: 'anthropic/claude-haiku-4.5', label: 'Claude Haiku 4.5' },
]

export default function useAiStudioSetup(show, taskKinds) {
  const [ready, setReady] = useState(null)   // null = probing
  const [options, setOptions] = useState([])
  const [planners, setPlanners] = useState([])
  const [resolution, setResolution] = useState(null)
  const [autoResolution, setAutoResolution] = useState(null)

  const hasLocalKey = Boolean(localStorage.getItem('openrouter_api_key'))

  useEffect(() => {
    if (!show) return
    let cancelled = false
    Promise.all([
      fetch(`${API_URL}/skin-lab/ai-status`).then((r) => r.json()),
      fetch(`${API_URL}/ai-engine/models`).then((r) => r.json()),
      fetch(`${API_URL}/ai-engine/status`).then((r) => r.json()).catch(() => ({})),
      fetch(`${API_URL}/ai-engine/planners`).then((r) => r.json()).catch(() => ({})),
    ]).then(([st, m, eng, p]) => {
      if (cancelled) return
      setReady(Boolean(st.hasKey || hasLocalKey || st.localModelReady))
      if (m.success) {
        const engineOk = Boolean(eng.engine?.installed && eng.engine?.ok)
        const keyOk = Boolean(st.hasKey || hasLocalKey)
        // locked models stay VISIBLE (greyed) so users learn what unlocks
        // them: local = engine installed + weights downloaded; api = a key
        setOptions(m.models.map((mm) => {
          let reason = null
          if (mm.kind === 'local') {
            if (!engineOk && !mm.downloaded) reason = 'install engine + download'
            else if (!engineOk) reason = 'install the engine'
            else if (!mm.downloaded) reason = mm.partial ? 'resume the download' : 'download it'
            else if (!mm.enabled) reason = 'disabled in settings'
            else if (mm.needsEngineUpdate) reason = 'needs engine update'
          } else if (mm.requiresKey && !keyOk) {
            reason = 'needs an OpenRouter key'
          }
          return {
            value: mm.kind === 'api' ? mm.repoId : mm.id,
            provider: mm.kind === 'api' ? 'openrouter' : 'local',
            locked: Boolean(reason),
            reason,
            label: mm.stats?.avgSeconds != null
              ? `${mm.label} — ~${Math.round(mm.stats.avgSeconds)}s/image`
              : mm.label,
          }
        }))
      }
      // planner list with locked/unlocked state, mirroring the image-model
      // picker: API planners need a key; installed Ollama models are free;
      // the recommended local LLM shows LOCKED until it's pulled
      const keyOk2 = Boolean(st.hasKey || hasLocalKey)
      const localList = (p.local || []).map((m) => ({
        id: `ollama:${m.name}`,
        label: `${m.name} — local LLM (free, offline)`,
        locked: false,
      }))
      if (p.recommended
          && !localList.some((l) => l.id === `ollama:${p.recommended.name}`)) {
        localList.push({
          id: `ollama:${p.recommended.name}`,
          label: `${p.recommended.name} — local LLM (free, offline)`,
          locked: true,
          reason: p.ollamaAvailable
            ? 'pull it in AI Studio setup'
            : 'set up local LLMs in AI Studio setup',
        })
      }
      setPlanners([
        ...API_PLANNERS.map((pl) => ({
          ...pl,
          locked: !keyOk2,
          reason: 'needs an OpenRouter key',
        })),
        ...localList,
      ])
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

  return { ready, options, planners, resolution, autoResolution, resolveFor }
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

/** Per-task "what will run" — ONE BOX PER TASK, so mod types that need the
 * stronger model (e.g. stage backdrops) get their own clearly-marked second
 * box, and mod types that don't simply don't show it. */
export function ResolutionNotice({ resolution }) {
  if (!resolution) return null
  return (
    <>
      {resolution.map((t) => (
        <div key={t.kind}
             className={`ai-studio-resolution${t.escalated || t.error ? ' escalated' : ''}`}>
          <div className={`ai-studio-progress-message${t.escalated || t.error ? ' escalated' : ''}`}>
            {TASK_LABELS[t.kind] || t.kind} → {t.error ? t.error : t.label}
          </div>
          {t.escalated && t.reason && (
            <div className="ai-studio-resolution-reason">{t.reason}</div>
          )}
        </div>
      ))}
    </>
  )
}

/** Telemetry-based runtime prediction shown before Generate. Character runs
 * are ~2-4 materials + planning; stage runs add the ISO build + Dolphin boot
 * (~2.5-3.5 min). Returns null until the resolved model has measured runs. */
export function TimeEstimate({ resolution, stage = false }) {
  if (!resolution) return null
  const material = resolution.find((t) => t.kind === 'material')
  const backdrop = resolution.find((t) => t.kind === 'backdrop')
  const a = material?.avgSeconds
  if (a == null) return null
  const b = backdrop?.avgSeconds ?? a
  const lo = stage ? Math.round(2 * a + b + 150) : Math.round(2 * a + 15)
  const hi = stage ? Math.round(3 * a + b + 220) : Math.round(4 * a + 35)
  const fmt = (s) => (s >= 90 ? `${Math.round(s / 60)} min` : `${s}s`)
  return (
    <div className="ai-studio-estimate">
      ⏱ estimated ~{fmt(lo)}–{fmt(hi)} (from your past runs)
    </div>
  )
}

const plannerName = (m) => (m || '').replace(/^ollama:/, '').split('/').pop()
const money = (v) => (v >= 0.01 ? `$${v.toFixed(2)}` : `${(v * 100).toFixed(1)}¢`)

/** Full cost & time breakdown for the preview phase — INCLUDING the planner
 * calls (an OpenRouter planner bills even when image models are local). */
export function CostBreakdown({ costInfo }) {
  if (!costInfo) return null
  const planning = costInfo.planning || []
  const gen = costInfo.generation || []
  if (!planning.length && !gen.length) return null
  const planCost = planning.reduce((s, p) => s + (p.costUsd || 0), 0)
  const totalSecs = gen.reduce((s, g) => s + (g.seconds || 0), 0)
  return (
    <div className="ai-studio-genlog">
      {planning.length > 0 && (
        <div className="ai-studio-cost-row">
          <span>
            planning — {plannerName(planning[0].model)}
            {planning.length > 1 ? ` ×${planning.length}` : ''}
          </span>
          <span>{planCost > 0 ? `~${money(planCost)}` : 'free (local)'}</span>
        </div>
      )}
      {gen.map((g, i) => (
        <div key={i} className="ai-studio-cost-row">
          <span>
            material {i + 1} — {plannerName(g.model)}
            {g.seconds != null ? ` — ${g.seconds}s` : ''}
            {g.escalated ? ' — escalated' : ''}
          </span>
          <span>
            {g.cached ? 'cached (free)'
              : g.estCostUsd > 0 ? `~${money(g.estCostUsd)}` : 'free (local)'}
          </span>
        </div>
      ))}
      <div className="ai-studio-cost-row total">
        <span>total · {totalSecs.toFixed(0)}s generating</span>
        <span>{costInfo.cost > 0 ? `~${money(costInfo.cost)}` : 'free'}</span>
      </div>
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
