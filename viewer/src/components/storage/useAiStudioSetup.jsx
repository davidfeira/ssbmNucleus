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
  const hasLocalKey = Boolean(localStorage.getItem('openrouter_api_key'))

  const [ready, setReady] = useState(null)   // null = probing
  const [options, setOptions] = useState([])
  // the API planners render INSTANTLY (their lock state is a best guess from
  // the localStorage key); /planners refines labels + appends local LLMs —
  // no empty dropdown popping in after the slow Ollama probe
  const [planners, setPlanners] = useState(() => API_PLANNERS.map((pl) => ({
    ...pl, locked: !hasLocalKey, reason: 'needs an OpenRouter key',
  })))
  const [resolution, setResolution] = useState(null)
  const [autoResolution, setAutoResolution] = useState(null)

  useEffect(() => {
    if (!show) return
    let cancelled = false
    const stPromise = fetch(`${API_URL}/skin-lab/ai-status`).then((r) => r.json())

    // gate + image options: fast local endpoints, render as soon as they land
    Promise.all([
      stPromise,
      fetch(`${API_URL}/ai-engine/models`).then((r) => r.json()),
      fetch(`${API_URL}/ai-engine/status`).then((r) => r.json()).catch(() => ({})),
    ]).then(([st, m, eng]) => {
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
    }).catch(() => { if (!cancelled) setReady(false) })

    // planner list refinement: /planners can be slower (it probes Ollama),
    // so it updates the already-rendered list instead of gating it.
    // API planners need a key; installed Ollama models are free; the
    // recommended local LLM shows LOCKED until it's pulled. Measured
    // s/plan + cost from telemetry replace guesswork once runs exist.
    Promise.all([
      stPromise.catch(() => ({})),
      fetch(`${API_URL}/ai-engine/planners`).then((r) => r.json()),
    ]).then(([st, p]) => {
      if (cancelled) return
      const keyOk2 = Boolean(st.hasKey || hasLocalKey)
      const speed = (id) => {
        const s = p.stats?.[id]
        if (!s) return ''
        const parts = []
        if (s.avgSeconds != null) parts.push(`~${Math.round(s.avgSeconds)}s`)
        if (s.avgCostUsd > 0) parts.push(`~${money(s.avgCostUsd)}`)
        return parts.length ? ` — ${parts.join(' · ')}/plan` : ''
      }
      const localList = (p.local || []).map((m) => ({
        id: `ollama:${m.name}`,
        label: `${m.name} — local LLM (free, offline)${speed(`ollama:${m.name}`)}`,
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
          label: `${pl.label}${speed(pl.id)}`,
          locked: !keyOk2,
          reason: 'needs an OpenRouter key',
        })),
        ...localList,
      ])
    }).catch(() => {})
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

  // `selected` is either one model id (applied to every task kind) or a
  // per-kind map like { material: '...', backdrop: '...' } when the studio
  // has a dropdown per task. '' / missing = Auto for that kind.
  const resolveFor = useCallback((selected) => {
    const modelFor = (kind) => (selected && typeof selected === 'object'
      ? selected[kind] : selected)
    const tasks = taskKinds.map((kind) => ({
      kind,
      model: modelFor(kind) || undefined,
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
        const allAuto = taskKinds.every((kind) => !modelFor(kind))
        if (allAuto) setAutoResolution(d.tasks)
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

/** Optional inspiration-image upload shared by the character + stage studios.
 * Downscales to a ≤1024px JPEG on a white canvas client-side: caps the
 * request body, and vision/image APIs 400 on exotic mimes (the backend
 * re-checks anyway). value = data URL | null. */
export function InspirationPicker({ value, name, onChange }) {
  const ingest = (file) => {
    if (!file || !file.type?.startsWith('image/')) return
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => {
        const scale = Math.min(1, 1024 / Math.max(img.width, img.height))
        const canvas = document.createElement('canvas')
        canvas.width = Math.max(1, Math.round(img.width * scale))
        canvas.height = Math.max(1, Math.round(img.height * scale))
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = '#fff'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        onChange(canvas.toDataURL('image/jpeg', 0.9), file.name)
      }
      img.src = reader.result
    }
    reader.readAsDataURL(file)
  }

  return (
    <>
      <label className="ai-studio-label">Inspiration image (optional)</label>
      {value ? (
        <div className="ai-studio-insp">
          <img src={value} alt="inspiration" />
          <span className="ai-studio-insp-name">{name}</span>
          <button className="ai-studio-insp-clear" title="Remove image"
                  onClick={() => onChange(null, '')}>
            ×
          </button>
        </div>
      ) : (
        <label className="ai-studio-drop"
               onDragOver={(e) => e.preventDefault()}
               onDrop={(e) => { e.preventDefault(); ingest(e.dataTransfer.files[0]) }}>
          <input type="file" accept="image/*" hidden
                 onChange={(e) => { ingest(e.target.files[0]); e.target.value = '' }} />
          Drop an image here or click to browse — its palette and patterns
          get woven in
        </label>
      )}
    </>
  )
}

/** 'Auto — <model>' for ONE task kind — the per-dropdown Auto label when a
 * studio has a separate picker per task. */
export function autoOptionLabelFor(autoResolution, kind) {
  const t = (autoResolution || []).find((x) => x.kind === kind
                                              && !x.error && x.label)
  return t ? `Auto — ${shortName(t.label)}` : 'Auto (recommended)'
}

/** Escalation/error notices ONLY. What each task runs on is already visible
 * in its own picker (the Auto option names the resolved model), so plain
 * "Materials → X" echo rows are noise — a row appears here only when the
 * resolver had to OVERRIDE the pick (escalation) or can't run it (error). */
export function ResolutionNotice({ resolution }) {
  const rows = (resolution || []).filter((t) => t.escalated || t.error)
  if (!rows.length) return null
  return (
    <>
      {rows.map((t) => (
        <div key={t.kind} className="ai-studio-resolution escalated">
          <div className="ai-studio-progress-message escalated">
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
