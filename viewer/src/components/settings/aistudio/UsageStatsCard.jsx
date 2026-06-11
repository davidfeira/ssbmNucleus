/**
 * UsageStatsCard - measured generation times + costs per model, from the
 * backend's ai_runs.jsonl ledger. Empty until the first generation runs.
 */
import { useCallback, useEffect, useState } from 'react'
import { fmtAgo } from './useAiEngine'

export default function UsageStatsCard({ API_URL, refreshKey }) {
  const [stats, setStats] = useState(null)

  const load = useCallback(() => {
    fetch(`${API_URL}/ai-engine/stats?days=90`)
      .then((r) => r.json())
      .then((d) => { if (d.success) setStats(d) })
      .catch(() => {})
  }, [API_URL])

  useEffect(() => { load() }, [load, refreshKey])

  if (!stats || !stats.perModel?.length) return null

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">Generation stats (90 days)</div>
      <table className="aistudio-stats-table">
        <thead>
          <tr>
            <th>model</th><th>runs</th><th>avg</th><th>median</th>
            <th>cached</th><th>last used</th><th>cost</th>
          </tr>
        </thead>
        <tbody>
          {stats.perModel.map((m) => (
            <tr key={`${m.provider}/${m.model}`}>
              <td className="aistudio-mono">{m.model}</td>
              <td>{m.runs}</td>
              <td>{m.avgSeconds != null ? `${m.avgSeconds}s` : '—'}</td>
              <td>{m.medianSeconds != null ? `${m.medianSeconds}s` : '—'}</td>
              <td>{m.cachedHits || 0}</td>
              <td>{fmtAgo(m.lastTs)}</td>
              <td>{m.totalCostUsd > 0 ? `$${m.totalCostUsd.toFixed(2)}` : 'free'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="aistudio-storage-footer">
        {stats.totals.runs} generations
        {stats.totals.costUsd > 0 ? ` · $${stats.totals.costUsd.toFixed(2)} total API spend` : ''}
      </div>
    </div>
  )
}
