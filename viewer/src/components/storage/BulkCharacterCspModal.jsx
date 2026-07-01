/**
 * BulkCharacterCspModal
 *
 * Bulk-retake a character's costume portraits: pick costumes, re-render each with
 * its active pose (through the persistent CSP render pool), review the
 * before/after grid, and apply the ones you keep. The character analog of
 * BulkStageCaptureModal; reuses the `.bulk-capture-*` styling (StorageViewer.css).
 * Flow: select -> retaking -> review (keep/discard each) -> apply.
 */
import { useEffect, useMemo } from 'react'
import { API_URL } from '../../config'
import { playSound, playHoverSound } from '../../utils/sounds'
import { useBulkCharacterCsp } from '../../hooks/useBulkCharacterCsp'

const imgBase = API_URL.replace('/api/mex', '')

// Current portrait URL for a costume (mirrors SkinCard.getCspUrl): the active
// custom-pose alternate if one is selected, else the default CSP.
function currentCspUrl(character, skin) {
  if (skin.active_csp_id && skin.alternate_csps) {
    const activeAlt = skin.alternate_csps.find((a) => a.id === skin.active_csp_id)
    if (activeAlt) return `${imgBase}/storage/${character}/${activeAlt.filename}`
  }
  return `${imgBase}/storage/${character}/${skin.csp_filename || `${skin.id}_csp.png`}`
}

export default function BulkCharacterCspModal({ show, character, skins, onApplied, onClose }) {
  const bulk = useBulkCharacterCsp({ character, onApplied })
  const {
    phase, selected, toggle, selectAll, clearSelection,
    progress, results, keep, toggleKeep, applying, error,
    startRetake, applyKept, reset,
  } = bulk

  useEffect(() => {
    if (show) reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  // Selectable costumes: real skins only (no folders / hidden).
  const costumes = useMemo(
    () => (skins || []).filter((s) => s.type !== 'folder' && s.visible !== false),
    [skins])
  const byId = useMemo(() => {
    const m = {}
    for (const s of costumes) m[s.id] = s
    return m
  }, [costumes])
  const nameOf = (id) => byId[id]?.name || byId[id]?.costume_code || id

  if (!show) return null

  const selectedCount = selected.size
  const okResults = results.filter((r) => r.ok)
  const keptCount = okResults.filter((r) => keep.has(r.skinId)).length
  const failed = results.filter((r) => !r.ok)
  const close = () => { playSound('back'); reset(); onClose() }

  return (
    <div className="bulk-capture-overlay" onClick={close}>
      <div className="bulk-capture-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="bulk-capture-header">
          <h2>Retake CSPs — {character}{phase === 'review' && ' — Review'}</h2>
          <button className="bulk-capture-close" onClick={close} title="Close">✕</button>
        </div>

        {error && <div className="bulk-capture-error">{error}</div>}

        {/* ---- SELECT ---- */}
        {phase === 'select' && (
          <>
            <div className="bulk-capture-toolbar">
              <button className="mode-btn" onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); selectAll(costumes.map((c) => c.id)) }}>
                Select all ({costumes.length})
              </button>
              <button className="mode-btn" onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); clearSelection() }}>Clear</button>
              <span className="bulk-capture-count">{selectedCount} selected</span>
            </div>

            <div className="bulk-capture-body">
              {costumes.length === 0
                ? <p className="bulk-capture-muted">No costumes to retake.</p>
                : (
                  <div className="bulk-capture-grid">
                    {costumes.map((s) => {
                      const sel = selected.has(s.id)
                      return (
                        <div key={s.id} onClick={() => { playSound('boop'); toggle(s.id) }}
                          onMouseEnter={playHoverSound}
                          className={`bulk-capture-card${sel ? ' selected' : ''}`}>
                          <div className="bulk-capture-thumb">
                            {s.has_csp
                              ? <img src={currentCspUrl(character, s)} alt={s.name} loading="lazy" />
                              : <span className="noshot">no CSP</span>}
                          </div>
                          <div className="bulk-capture-card-label">
                            <span>{sel ? '☑ ' : '☐ '}{s.name}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
            </div>

            <div className="bulk-capture-footer">
              <button className="mode-btn" onClick={close}>Cancel</button>
              <button className="mode-btn mode-btn-primary" disabled={selectedCount === 0}
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); startRetake([...selected]) }}
                style={{ opacity: selectedCount === 0 ? 0.5 : 1 }}>
                Retake {selectedCount || ''} selected
              </button>
            </div>
          </>
        )}

        {/* ---- RETAKING ---- */}
        {phase === 'retaking' && (
          <div className="bulk-capture-progress-wrap">
            <p style={{ marginBottom: '1rem' }}>{progress?.message || 'Retaking…'}</p>
            <div className="bulk-capture-progress-bar">
              <div className="bulk-capture-progress-fill"
                style={{ width: `${progress ? (progress.done / Math.max(1, progress.total)) * 100 : 0}%` }} />
            </div>
            <p className="bulk-capture-muted" style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              Rendering each costume with its active pose — nothing is saved yet.
            </p>
          </div>
        )}

        {/* ---- REVIEW (before -> after) ---- */}
        {phase === 'review' && (
          <>
            <div className="bulk-capture-review-note">
              Keep the retakes you want, then apply. {keptCount} of {okResults.length} kept.
            </div>
            {failed.length > 0 && (
              <div className="bulk-capture-diagnostics">
                <strong>{failed.length} failed</strong>
                <ul>
                  {failed.map((r) => (
                    <li key={r.skinId}><span>{nameOf(r.skinId)}</span><em>{r.error || 'render failed'}</em></li>
                  ))}
                </ul>
              </div>
            )}
            <div className="bulk-capture-review-grid">
              {okResults.map((r) => {
                const kept = keep.has(r.skinId)
                const skin = byId[r.skinId]
                return (
                  <div key={r.skinId}
                    className={`bulk-capture-card${kept ? ' selected' : ''}`}>
                    <div className="bulk-capture-thumb bulk-capture-beforeafter"
                      style={{ cursor: 'pointer' }}
                      onClick={() => toggleKeep(r.skinId)}>
                      {skin && skin.has_csp
                        ? <img src={currentCspUrl(character, skin)} alt="before" loading="lazy" />
                        : <span className="noshot">—</span>}
                      <span className="bulk-capture-arrow">→</span>
                      <img src={r.dataUri} alt="after" />
                    </div>
                    <div className="bulk-capture-card-label">
                      <input type="checkbox" checked={kept} onChange={() => toggleKeep(r.skinId)} />
                      <span>{nameOf(r.skinId)}{r.poseName && r.poseName !== 'Default' ? ` (${r.poseName})` : ''}</span>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="bulk-capture-footer">
              <button className="mode-btn" onClick={() => { playSound('boop'); reset() }} disabled={applying}>
                Discard all
              </button>
              <button className="mode-btn mode-btn-primary" disabled={applying || keptCount === 0}
                onMouseEnter={playHoverSound}
                onClick={async () => { try { await applyKept() } finally { close() } }}
                style={{ opacity: applying || keptCount === 0 ? 0.5 : 1 }}>
                {applying ? 'Applying…' : `Apply ${keptCount || ''}`}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
