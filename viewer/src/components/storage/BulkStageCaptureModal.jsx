/**
 * BulkStageCaptureModal
 *
 * Pick DAS variants from across the whole vault and screenshot them in bulk. The
 * backend groups the selection by base stage and packs up to 4 per ISO (X/Y/Z/L
 * holds) so one boot captures four at a time. Flow: select -> capturing -> review
 * (keep/discard each) -> save the kept shots as the variants' previews.
 *
 * Styling lives in StorageViewer.css (.bulk-capture-*), responsive down to
 * phone-ish widths (full-bleed modal + tighter tiles under 760px).
 */
import { useEffect, useMemo } from 'react'
import { API_URL } from '../../config'
import { playSound, playHoverSound } from '../../utils/sounds'
import { useBulkStageCapture } from '../../hooks/useBulkStageCapture'
import DolphinEmbedPanel from '../shared/DolphinEmbedPanel'

const STAGE_ORDER = ['Battlefield', 'Final Destination', 'Dreamland', "Yoshi's Story",
  'Pokemon Stadium', 'Fountain of Dreams']
const imgBase = API_URL.replace('/api/mex', '')

export default function BulkStageCaptureModal({ show, onClose, onSaved }) {
  const bulk = useBulkStageCapture({ onSaved })
  const {
    phase, variants, loading, error, selected, toggle, setMany, clearSelection, keyOf,
    progress, results, keep, toggleKeep, saving, captureLog, captureFailures,
    captureAttempts, loadVariants, startCapture, saveKept, reset,
  } = bulk

  useEffect(() => {
    if (show) { reset(); loadVariants() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show])

  // Group variants by stage for display.
  const grouped = useMemo(() => {
    const g = {}
    for (const v of variants) (g[v.stageName] = g[v.stageName] || []).push(v)
    const names = Object.keys(g).sort(
      (a, b) => (STAGE_ORDER.indexOf(a) + 99) - (STAGE_ORDER.indexOf(b) + 99))
    return names.map((name) => [name, g[name]])
  }, [variants])

  if (!show) return null

  const selectedCount = selected.size
  const missing = variants.filter((v) => !v.hasScreenshot)
  const keptCount = results.filter((r) => r.ok && r.screenshot && keep.has(r.variantId)).length
  const failedCount = captureFailures.length || results.filter((r) => !r.ok).length
  const diagnosticLog = captureLog.length ? captureLog : captureAttempts.flatMap((a) => [
    `[${a.attempt || 'attempt'}] ${a.reason || 'failed'}`,
    ...(a.log || []).map((line) => `  ${line}`),
  ])
  const close = () => { playSound('back'); reset(); onClose() }

  return (
    <div className="bulk-capture-overlay" onClick={close}>
      <div className="bulk-capture-modal" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="bulk-capture-header">
          <h2>
            Bulk Stage Screenshots
            {phase === 'review' && ' — Review'}
          </h2>
          <button className="bulk-capture-close" onClick={close} title="Close">✕</button>
        </div>

        {error && <div className="bulk-capture-error">{error}</div>}
        {error && diagnosticLog.length > 0 && (
          <details className="bulk-capture-log">
            <summary>Capture log</summary>
            <pre>{diagnosticLog.join('\n')}</pre>
          </details>
        )}

        {/* ---- SELECT ---- */}
        {phase === 'select' && (
          <>
            <div className="bulk-capture-toolbar">
              <button className="mode-btn" onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); setMany(missing, true) }}>
                Select all missing ({missing.length})
              </button>
              <button className="mode-btn" onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); setMany(variants, true) }}>
                Select all ({variants.length})
              </button>
              <button className="mode-btn" onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); clearSelection() }}>Clear</button>
              <span className="bulk-capture-count">{selectedCount} selected</span>
            </div>

            <div className="bulk-capture-body">
              {loading ? <p className="bulk-capture-muted">Loading variants…</p>
                : grouped.length === 0 ? <p className="bulk-capture-muted">No DAS variants in your vault.</p>
                : grouped.map(([stageName, vs]) => (
                  <div key={stageName} className="bulk-capture-stage">
                    <div className="bulk-capture-stage-head">
                      <strong>{stageName}</strong>
                      <span className="bulk-capture-muted">({vs.length})</span>
                      <button className="mode-btn" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}
                        onClick={() => { playSound('boop'); setMany(vs, !vs.every((v) => selected.has(keyOf(v)))) }}>
                        toggle
                      </button>
                    </div>
                    <div className="bulk-capture-grid">
                      {vs.map((v) => {
                        const sel = selected.has(keyOf(v))
                        return (
                          <div key={keyOf(v)} onClick={() => { playSound('boop'); toggle(v) }}
                            onMouseEnter={playHoverSound}
                            className={`bulk-capture-card${sel ? ' selected' : ''}`}>
                            <div className="bulk-capture-thumb">
                              {v.hasScreenshot ? (
                                <img src={`${imgBase}${v.screenshotUrl}`} alt={v.name} loading="lazy" />
                              ) : (
                                <span className="noshot">no shot</span>
                              )}
                            </div>
                            <div className="bulk-capture-card-label">
                              <span>{sel ? '☑ ' : '☐ '}{v.name}</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
            </div>

            <div className="bulk-capture-footer">
              <button className="mode-btn" onClick={close}>Cancel</button>
              <button className="mode-btn mode-btn-primary" disabled={selectedCount === 0}
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); startCapture() }}
                style={{ opacity: selectedCount === 0 ? 0.5 : 1 }}>
                Capture {selectedCount || ''} selected
              </button>
            </div>
          </>
        )}

        {/* ---- CAPTURING ---- */}
        {phase === 'capturing' && (
          <div className="bulk-capture-progress-wrap">
            <p style={{ marginBottom: '1rem' }}>{progress?.message || 'Capturing…'}</p>
            <div className="bulk-capture-progress-bar">
              <div className="bulk-capture-progress-fill"
                style={{ width: `${progress?.percentage || 0}%` }} />
            </div>
            <DolphinEmbedPanel active fill />
            <p className="bulk-capture-muted" style={{ marginTop: '0.5rem', fontSize: '0.8rem', flex: '0 0 auto' }}>
              {progress?.percentage || 0}% — your Slippi setup is untouched
            </p>
          </div>
        )}

        {/* ---- REVIEW ---- */}
        {phase === 'review' && (
          <>
            <div className="bulk-capture-review-note">
              Keep the shots you want, then save. {keptCount} of {results.filter((r) => r.ok).length} kept.
            </div>
            {failedCount > 0 && (
              <div className="bulk-capture-diagnostics">
                <strong>{failedCount} failed</strong>
                <ul>
                  {(captureFailures.length ? captureFailures : results.filter((r) => !r.ok)).map((r) => (
                    <li key={`${r.stageCode}:${r.variantId}`}>
                      <span>{r.name || r.variantId}</span>
                      <em>{r.reason || 'capture failed'}</em>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {diagnosticLog.length > 0 && (
              <details className="bulk-capture-log">
                <summary>Capture log</summary>
                <pre>{diagnosticLog.join('\n')}</pre>
              </details>
            )}
            <div className="bulk-capture-review-grid">
              {results.map((r) => (
                <div key={`${r.stageCode}:${r.variantId}`}
                  className={`bulk-capture-card${r.ok && keep.has(r.variantId) ? ' selected' : ''}${r.ok ? '' : ' failed'}`}>
                  <div className="bulk-capture-thumb"
                    style={{ cursor: r.ok ? 'pointer' : 'default' }}
                    onClick={() => r.ok && toggleKeep(r.variantId)}>
                    {r.ok && r.screenshot
                      ? <img src={r.screenshot} alt={r.name} />
                      : <span className="failreason">{r.reason || 'failed'}</span>}
                  </div>
                  <div className="bulk-capture-card-label">
                    {r.ok && (
                      <input type="checkbox" checked={keep.has(r.variantId)}
                        onChange={() => toggleKeep(r.variantId)} />
                    )}
                    <span>{r.name}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="bulk-capture-footer">
              <button className="mode-btn" onClick={() => { playSound('boop'); reset() }} disabled={saving}>
                Discard all
              </button>
              <button className="mode-btn mode-btn-primary" disabled={saving || keptCount === 0}
                onMouseEnter={playHoverSound}
                onClick={async () => { const n = await saveKept(); if (n) close() }}
                style={{ opacity: saving || keptCount === 0 ? 0.5 : 1 }}>
                {saving ? 'Saving…' : `Save ${keptCount || ''}`}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
