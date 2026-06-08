/**
 * BulkStageCaptureModal
 *
 * Pick DAS variants from across the whole vault and screenshot them in bulk. The
 * backend groups the selection by base stage and packs up to 4 per ISO (X/Y/Z/L
 * holds) so one boot captures four at a time. Flow: select -> capturing -> review
 * (keep/discard each) -> save the kept shots as the variants' previews.
 */
import { useEffect, useMemo } from 'react'
import { API_URL } from '../../config'
import { playSound, playHoverSound } from '../../utils/sounds'
import { useBulkStageCapture } from '../../hooks/useBulkStageCapture'

const STAGE_ORDER = ['Battlefield', 'Final Destination', 'Dreamland', "Yoshi's Story",
  'Pokemon Stadium', 'Fountain of Dreams']
const imgBase = API_URL.replace('/api/mex', '')

export default function BulkStageCaptureModal({ show, onClose, onSaved }) {
  const bulk = useBulkStageCapture({ onSaved })
  const {
    phase, variants, loading, error, selected, toggle, setMany, clearSelection, keyOf,
    progress, results, keep, toggleKeep, saving, loadVariants, startCapture, saveKept, reset,
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
  const close = () => { playSound('back'); reset(); onClose() }

  return (
    <div className="bulk-capture-overlay" onClick={close}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2vh 2vw' }}>
      <div className="bulk-capture-modal" onClick={(e) => e.stopPropagation()}
        style={{ background: 'var(--color-bg-secondary, #1c1c24)', borderRadius: 12,
          width: 'min(1040px, 94vw)', maxWidth: 'min(1040px, 94vw)',
          height: 'min(860px, 90vh)', maxHeight: '90vh',
          display: 'flex', flexDirection: 'column',
          border: '1px solid var(--color-border, #333)', overflow: 'hidden' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '1rem 1.25rem', borderBottom: '1px solid var(--color-border, #333)' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
            Bulk Stage Screenshots
            {phase === 'review' && ' — Review'}
          </h2>
          <button className="btn-edit" onClick={close} title="Close" style={{ fontSize: '1.1rem' }}>✕</button>
        </div>

        {error && (
          <div style={{ padding: '0.6rem 1.25rem', color: 'var(--color-danger, #ff6b6b)',
            background: 'rgba(255,0,0,0.08)' }}>{error}</div>
        )}

        {/* ---- SELECT ---- */}
        {phase === 'select' && (
          <>
            <div style={{ display: 'flex', gap: '0.5rem', padding: '0.75rem 1.25rem',
              borderBottom: '1px solid var(--color-border, #333)', flexWrap: 'wrap', alignItems: 'center' }}>
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
              <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted, #999)', fontSize: '0.85rem' }}>
                {selectedCount} selected
              </span>
            </div>

            <div style={{ overflowY: 'auto', padding: '0.75rem 1.25rem', flex: 1 }}>
              {loading ? <p style={{ color: 'var(--color-text-muted, #999)' }}>Loading variants…</p>
                : grouped.length === 0 ? <p style={{ color: 'var(--color-text-muted, #999)' }}>No DAS variants in your vault.</p>
                : grouped.map(([stageName, vs]) => (
                  <div key={stageName} style={{ marginBottom: '1.1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                      <strong>{stageName}</strong>
                      <span style={{ color: 'var(--color-text-muted, #999)', fontSize: '0.8rem' }}>
                        ({vs.length})
                      </span>
                      <button className="mode-btn" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}
                        onClick={() => { playSound('boop'); setMany(vs, !vs.every((v) => selected.has(keyOf(v)))) }}>
                        toggle
                      </button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.5rem' }}>
                      {vs.map((v) => {
                        const sel = selected.has(keyOf(v))
                        return (
                          <div key={keyOf(v)} onClick={() => { playSound('boop'); toggle(v) }}
                            onMouseEnter={playHoverSound}
                            style={{ cursor: 'pointer', borderRadius: 8, overflow: 'hidden',
                              border: `2px solid ${sel ? 'var(--color-accent, #6c8cff)' : 'transparent'}`,
                              background: 'var(--color-bg-tertiary, #25252e)', position: 'relative' }}>
                            <div style={{ aspectRatio: '4/3', background: '#000',
                              display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              {v.hasScreenshot ? (
                                <img src={`${imgBase}${v.screenshotUrl}`} alt={v.name}
                                  style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                              ) : (
                                <span style={{ color: '#666', fontSize: '0.75rem' }}>no shot</span>
                              )}
                            </div>
                            <div style={{ padding: '0.25rem 0.4rem', fontSize: '0.72rem',
                              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {sel ? '☑ ' : '☐ '}{v.name}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
            </div>

            <div style={{ padding: '0.85rem 1.25rem', borderTop: '1px solid var(--color-border, #333)',
              display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
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
          <div style={{ padding: '2.5rem 1.5rem', textAlign: 'center' }}>
            <p style={{ marginBottom: '1rem' }}>{progress?.message || 'Capturing…'}</p>
            <div style={{ height: 10, background: 'var(--color-bg-tertiary, #25252e)', borderRadius: 6, overflow: 'hidden' }}>
              <div style={{ width: `${progress?.percentage || 0}%`, height: '100%',
                background: 'var(--color-accent, #6c8cff)', transition: 'width 0.3s' }} />
            </div>
            <p style={{ marginTop: '0.5rem', color: 'var(--color-text-muted, #999)', fontSize: '0.8rem' }}>
              {progress?.percentage || 0}% — your Slippi setup is untouched
            </p>
          </div>
        )}

        {/* ---- REVIEW ---- */}
        {phase === 'review' && (
          <>
            <div style={{ padding: '0.6rem 1.25rem', borderBottom: '1px solid var(--color-border, #333)',
              color: 'var(--color-text-muted, #999)', fontSize: '0.85rem' }}>
              Keep the shots you want, then save. {keptCount} of {results.filter((r) => r.ok).length} kept.
            </div>
            <div style={{ overflowY: 'auto', padding: '0.75rem 1.25rem', flex: 1,
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.6rem' }}>
              {results.map((r) => (
                <div key={`${r.stageCode}:${r.variantId}`}
                  style={{ borderRadius: 8, overflow: 'hidden', background: 'var(--color-bg-tertiary, #25252e)',
                    border: `2px solid ${r.ok && keep.has(r.variantId) ? 'var(--color-accent, #6c8cff)' : 'transparent'}`,
                    opacity: r.ok ? 1 : 0.55 }}>
                  <div style={{ aspectRatio: '4/3', background: '#000', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', cursor: r.ok ? 'pointer' : 'default' }}
                    onClick={() => r.ok && toggleKeep(r.variantId)}>
                    {r.ok && r.screenshot
                      ? <img src={r.screenshot} alt={r.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      : <span style={{ color: '#ff6b6b', fontSize: '0.75rem', padding: '0.5rem', textAlign: 'center' }}>
                          {r.reason || 'failed'}</span>}
                  </div>
                  <div style={{ padding: '0.3rem 0.45rem', fontSize: '0.72rem', display: 'flex',
                    alignItems: 'center', gap: '0.3rem', whiteSpace: 'nowrap', overflow: 'hidden' }}>
                    {r.ok && (
                      <input type="checkbox" checked={keep.has(r.variantId)}
                        onChange={() => toggleKeep(r.variantId)} />
                    )}
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.name}</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ padding: '0.85rem 1.25rem', borderTop: '1px solid var(--color-border, #333)',
              display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
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
