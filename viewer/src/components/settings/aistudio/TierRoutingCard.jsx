/**
 * TierRoutingCard - map task tiers to models. 'Standard' covers seamless
 * material swatches; 'Strong' covers coherent scene work (stage backdrops),
 * where the studios escalate past tile-only locals — this is where the user
 * decides whether that escalation goes to a bigger local model or the API.
 */
import { useEffect, useState } from 'react'
import { playSound } from '../../../utils/sounds'

const TIERS = [
  { key: 'standard', label: 'Standard — material tiles',
    hint: 'seamless swatches for costumes & stage surfaces; any model copes' },
  { key: 'strong', label: 'Strong — scenes & backgrounds',
    hint: 'stage backdrops need one coherent image; fast tile models produce mush' },
]

export default function TierRoutingCard({ API_URL, status, models, hasKey, onChanged }) {
  const [routing, setRouting] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    setRouting(status?.routing || null)
  }, [status])

  if (!models) return null

  const usable = models.models.filter((m) => (
    m.kind === 'local' ? (m.downloaded && m.enabled && !m.needsEngineUpdate)
      : hasKey))
  const valueOf = (target) => target?.model || ''

  const setTier = async (tier, modelValue) => {
    const body = { [tier]: modelValue ? { model: modelValue } : null }
    try {
      const res = await fetch(`${API_URL}/ai-engine/routing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (data.success) {
        setRouting(data.routing)
        playSound('boop')
        setMessage('Saved')
        setTimeout(() => setMessage(''), 2000)
        onChanged?.()
      } else {
        setMessage(data.error || 'save failed')
      }
    } catch (err) {
      setMessage(err.message)
    }
  }

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">Which model handles what</div>
      <p className="section-description">
        The studios route each generation by how demanding it is. When a
        strong task needs a better model than your standard pick, the studio
        tells you before it generates.
      </p>
      {TIERS.map((tier) => {
        const optionValue = (m) => (m.kind === 'api' ? m.repoId : m.id)
        return (
          <div key={tier.key} className="aistudio-tier-row">
            <div className="aistudio-tier-label">
              <div>{tier.label}</div>
              <div className="aistudio-tier-hint">{tier.hint}</div>
            </div>
            <select
              className="ai-studio-planner"
              value={valueOf(routing?.[tier.key])}
              onChange={(e) => setTier(tier.key, e.target.value)}
            >
              <option value="">Auto (recommended)</option>
              {usable.map((m) => (
                <option key={m.id} value={optionValue(m)}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        )
      })}
      {message && <div className="message success">{message}</div>}
    </div>
  )
}
