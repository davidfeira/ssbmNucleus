/**
 * UsageStatsCard - measured generation times + costs per model, from the
 * backend's ai_runs.jsonl ledger. Empty until the first generation runs.
 * Stats are ALL-TIME; the Reset button moves the ledger aside and starts
 * fresh (it also resets the measured s/plan & cost hints in the pickers).
 */
import { useCallback, useEffect, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'
import { appConfirm } from '../../../utils/appDialogs'
import { fmtAgo } from './useAiEngine'

export default function UsageStatsCard({ API_URL, refreshKey }) {
  const [stats, setStats] = useState(null)

  const load = useCallback(() => {
    fetch(`${API_URL}/ai-engine/stats`)
      .then((r) => r.json())
      .then((d) => { if (d.success) setStats(d) })
      .catch(() => {})
  }, [API_URL])

  useEffect(() => { load() }, [load, refreshKey])

  const reset = async () => {
    if (!await appConfirm(
      'Reset all generation stats? The measured speed/cost hints in the model pickers start over.',
      {
        title: 'Reset Stats',
        confirmText: 'Reset',
      }
    )) return
    try {
      const res = await fetch(`${API_URL}/ai-engine/stats/reset`,
                              { method: 'POST' })
      const d = await res.json()
      if (d.success) {
        playSound('boop')
        load()
      }
    } catch { /* leave the table as-is */ }
  }

  if (!stats || !stats.perModel?.length) return null

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        Generation stats
        <button className="aistudio-linkbtn" style={{ marginLeft: 'auto' }}
                onMouseEnter={playHoverSound} onClick={reset}>
          Reset
        </button>
      </div>
      <table className="aistudio-stats-table">
        <thead>
          <tr>
            <th>model</th><th>runs</th><th>avg</th><th>median</th>
            <th>last used</th><th>cost</th>
          </tr>
        </thead>
        <tbody>
          {stats.perModel.map((m) => (
            <tr key={`${m.provider}/${m.model}`}>
              <td className="aistudio-mono">{m.model}</td>
              <td>{m.runs}</td>
              <td>{m.avgSeconds != null ? `${m.avgSeconds}s` : '—'}</td>
              <td>{m.medianSeconds != null ? `${m.medianSeconds}s` : '—'}</td>
              <td>{fmtAgo(m.lastTs)}</td>
              <td>{m.totalCostUsd > 0 ? `$${m.totalCostUsd.toFixed(2)}` : 'free'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="aistudio-storage-footer">
        {stats.totals.runs} generations · all time
        {stats.totals.costUsd > 0 ? ` · $${stats.totals.costUsd.toFixed(2)} total API spend` : ''}
      </div>
    </div>
  )
}
